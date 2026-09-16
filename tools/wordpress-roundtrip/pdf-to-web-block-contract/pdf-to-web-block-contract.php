<?php
/**
 * Plugin Name: PDF to Web block contract test
 * Description: Validation-only registrations for the WSU hero and section serialization contract.
 * Version: 0.1.0
 */

add_action('init', function () {
    wp_register_script(
        'pdf-to-web-block-contract',
        plugins_url('blocks.js', __FILE__),
        array('wp-blocks', 'wp-block-editor', 'wp-element'),
        '0.1.0',
        true
    );

    register_block_type('wsuwp/hero', array(
        'editor_script' => 'pdf-to-web-block-contract',
        'attributes' => array(
            'title' => array('type' => 'string'),
            'headingTag' => array('type' => 'string', 'default' => 'h1'),
            'caption' => array('type' => 'string'),
            'imageId' => array('type' => 'number'),
            'imageSrc' => array('type' => 'string'),
            'backgroundType' => array('type' => 'string'),
            'className' => array('type' => 'string'),
        ),
        'render_callback' => function ($attributes) {
            $tag = isset($attributes['headingTag']) ? $attributes['headingTag'] : 'h1';
            return sprintf('<%1$s>%2$s</%1$s>', esc_attr($tag), esc_html($attributes['title'] ?? ''));
        },
    ));

    register_block_type('wsuwp/section', array(
        'editor_script' => 'pdf-to-web-block-contract',
        'attributes' => array(
            'id' => array('type' => 'string'),
            'className' => array('type' => 'string'),
        ),
    ));
});
