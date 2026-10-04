"""Owned shutdown admission, authentication, streaming and background work."""
import asyncio
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
from fastapi import Request

import test_export_media_journey_independent as fixtures
from pdf_to_web import image_drafts
from pdf_to_web.app_lifecycle import OwnedServerLifecycle
from pdf_to_web.web import SESSION_COOKIE, WebAppConfig, create_app, run_server


class AppLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.stop = Mock()
        self.lifecycle = OwnedServerLifecycle(self.stop)
        self.config = WebAppConfig(port=54321, recent_store=Path(tmp.name) / 'recent.json',
                                   session_token='fixture-session', csrf_token='fixture-csrf')
        self.headers = {'origin': 'http://127.0.0.1:54321', 'x-csrf-token': self.config.csrf_token}

    def client(self, app, config=None, *, authenticated=True):
        config = config or self.config
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://127.0.0.1:54321',
                                cookies={SESSION_COOKIE: config.session_token} if authenticated else None)

    async def quit(self, client, **kwargs):
        return await client.post('/api/quit', headers=kwargs.pop('headers', self.headers),
                                 json=kwargs.pop('json', {'confirm': True}), **kwargs)

    async def test_quit_requires_session_origin_csrf_and_explicit_boolean_confirmation(self):
        app = create_app(self.config, lifecycle=self.lifecycle)
        async with self.client(app, authenticated=False) as client:
            self.assertEqual((await self.quit(client)).status_code, 401)
            self.assertEqual((await client.get('/api/lifecycle')).status_code, 401)
        async with self.client(app) as client:
            for headers in [{}, {**self.headers, 'origin': 'http://other.invalid'},
                            {**self.headers, 'x-csrf-token': 'wrong'}]:
                self.assertEqual((await self.quit(client, headers=headers)).status_code, 403)
            for value in [{}, {'confirm': False}, {'confirm': 'true'}, []]:
                self.assertEqual((await self.quit(client, json=value)).status_code, 400)
            self.assertEqual((await client.get('/api/lifecycle')).json()['state'], 'running')
        self.stop.assert_not_called()

    async def test_external_server_has_no_shutdown_capability(self):
        app = create_app(self.config)
        async with self.client(app) as client:
            self.assertFalse((await client.get('/api/lifecycle')).json()['available'])
            result = await self.quit(client)
            self.assertEqual(result.status_code, 409)
            self.assertIn('externally managed', result.text)
            self.assertEqual((await client.get('/')).status_code, 200)
        self.stop.assert_not_called()

    async def test_quit_is_atomic_and_refuses_later_work_without_running_handlers(self):
        app = create_app(self.config, lifecycle=self.lifecycle)
        mutation = Mock()
        @app.post('/fixture-mutation')
        async def change():
            mutation()
            return {'status': 'ok'}
        async with self.client(app) as client:
            results = await asyncio.gather(self.quit(client), self.quit(client))
            self.assertEqual(sorted(r.status_code for r in results), [200, 409])
            self.stop.assert_called_once_with()
            self.assertEqual((await client.post('/fixture-mutation')).status_code, 409)
            mutation.assert_not_called()
            self.assertEqual((await client.get('/api/lifecycle')).json()['state'], 'stopping')

    async def test_failed_owned_callback_reports_recovery_and_allows_work_and_retry(self):
        self.stop.side_effect = [RuntimeError('fixture failure'), None]
        app = create_app(self.config, lifecycle=self.lifecycle)
        async with self.client(app) as client:
            self.assertEqual((await self.quit(client)).status_code, 200)
            state = (await client.get('/api/lifecycle')).json()
            self.assertEqual(state['state'], 'running')
            self.assertIn('could not stop', state['error'])
            self.assertEqual((await client.get('/')).status_code, 200)
            self.assertEqual((await self.quit(client)).status_code, 200)
            self.assertEqual(self.stop.call_count, 2)

    async def test_partial_request_body_finishes_intact_before_quit(self):
        app = create_app(self.config, lifecycle=self.lifecycle)
        entered, release = asyncio.Event(), asyncio.Event()
        bodies = []
        @app.post('/fixture-body')
        async def body(request: Request):
            bodies.append(await request.body())
            return {'status': 'ok'}
        async def chunks():
            yield b'first-'
            entered.set()
            await release.wait()
            yield b'last'
        async with self.client(app) as client:
            work = asyncio.create_task(client.post('/fixture-body', content=chunks()))
            try:
                await asyncio.wait_for(entered.wait(), 3)
                self.assertEqual((await self.quit(client)).status_code, 409)
                self.stop.assert_not_called()
            finally:
                release.set()
            self.assertEqual((await work).status_code, 200)
            self.assertEqual(bodies, [b'first-last'])
            self.assertEqual((await self.quit(client)).status_code, 200)

    async def test_actual_export_zip_holds_busy_until_asgi_body_delivery_completes(self):
        fixture = fixtures.IndependentExportMediaJourneyTests()
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        fixture.model(2)
        item = next(d for d in fixture.prepare().json()['downloads'] if d['path'].endswith('.zip'))
        app = create_app(fixture.config, lifecycle=self.lifecycle)
        entered, release = asyncio.Event(), asyncio.Event()
        async def gated(scope, receive, send):
            async def gate(message):
                if scope['path'].startswith('/download/') and message['type'] == 'http.response.body' and message.get('body'):
                    entered.set()
                    await release.wait()
                await send(message)
            await app(scope, receive, gate)
        async with self.client(gated, fixture.config) as client:
            work = asyncio.create_task(client.get(item['url']))
            try:
                await asyncio.wait_for(entered.wait(), 3)
                self.assertEqual((await client.post('/api/quit', headers=fixture.headers, json={'confirm': True})).status_code, 409)
                self.stop.assert_not_called()
            finally:
                release.set()
            response = await work
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, (fixture.root / item['path']).read_bytes())
            self.assertEqual((await client.get('/api/lifecycle')).json()['active_work'], 0)
            self.assertEqual((await client.post('/api/quit', headers=fixture.headers, json={'confirm': True})).status_code, 200)

    async def test_running_and_queued_generation_blocks_quit_until_all_complete(self):
        fixture = fixtures.IndependentExportMediaJourneyTests()
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        model = fixture.model(3)
        app = create_app(fixture.config, lifecycle=self.lifecycle)
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        running = 0
        lock = threading.Lock()
        def generate(provider, entry, asset):
            nonlocal running
            with lock:
                running += 1
                if running == 2:
                    entered.set()
            release.wait(3)
            return fixture.fixture.response(entry)['responses'][0]
        with patch.object(image_drafts.OllamaProvider, 'generate', generate):
            async with self.client(app, fixture.config) as client:
                response = await client.post('/api/image-drafts/generate', headers=fixture.headers,
                    json={'document_id': model['output_pages']['project_id'], 'block_ids': ['image-0', 'image-1', 'image-2'], 'model': 'fixture-model'})
                self.assertEqual(response.status_code, 200, response.text)
                try:
                    self.assertTrue(await asyncio.to_thread(entered.wait, 3))
                    self.assertEqual((await client.get('/api/lifecycle')).json()['active_work'], 3)
                    self.assertEqual((await client.post('/api/quit', headers=fixture.headers, json={'confirm': True})).status_code, 409)
                    self.stop.assert_not_called()
                finally:
                    release.set()
                for _ in range(100):
                    if (await client.get('/api/lifecycle')).json()['active_work'] == 0:
                        break
                    await asyncio.sleep(.01)
                self.assertEqual((await client.get('/api/lifecycle')).json()['active_work'], 0)
                self.assertEqual((await client.post('/api/quit', headers=fixture.headers, json={'confirm': True})).status_code, 200)


class OwnedRunnerTests(unittest.TestCase):
    def test_runner_binds_only_its_own_server_and_returns_normally(self):
        own = Mock(should_exit=False)
        unrelated = Mock(should_exit=False)
        seen = {}
        def app(config, *, lifecycle):
            seen['lifecycle'] = lifecycle
            return 'fixture-app'
        def run():
            seen['lifecycle'].prepare_quit()
            seen['lifecycle'].stop()
        own.run.side_effect = run
        with patch('pdf_to_web.web.create_app', side_effect=app), patch('uvicorn.Config') as config, patch('uvicorn.Server', return_value=own) as server:
            run_server(None, '127.0.0.1', 54321, open_browser=False)
        config.assert_called_once_with('fixture-app', host='127.0.0.1', port=54321, log_level='info')
        server.assert_called_once_with(config.return_value)
        self.assertTrue(own.should_exit)
        self.assertFalse(unrelated.should_exit)


if __name__ == '__main__':
    unittest.main()
