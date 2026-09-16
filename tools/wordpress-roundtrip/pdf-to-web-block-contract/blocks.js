(function (blocks, blockEditor, element) {
    var el = element.createElement;
    var InnerBlocks = blockEditor.InnerBlocks;

    blocks.registerBlockType('wsuwp/hero', {
        apiVersion: 2,
        title: 'WSU Hero Contract',
        category: 'design',
        attributes: {
            title: { type: 'string' },
            headingTag: { type: 'string', default: 'h1' },
            caption: { type: 'string' },
            imageId: { type: 'number' },
            imageSrc: { type: 'string' },
            backgroundType: { type: 'string' },
            className: { type: 'string' }
        },
        edit: function (props) {
            return el('div', {}, el(props.attributes.headingTag || 'h1', {}, props.attributes.title));
        },
        save: function () { return null; }
    });

    blocks.registerBlockType('wsuwp/section', {
        apiVersion: 2,
        title: 'WSU Section Contract',
        category: 'design',
        attributes: {
            id: { type: 'string' },
            className: { type: 'string' }
        },
        edit: function () { return el('div', {}, el(InnerBlocks)); },
        save: function () { return el(InnerBlocks.Content); }
    });
}(window.wp.blocks, window.wp.blockEditor, window.wp.element));
