<?php

declare(strict_types=1);

$finder = PhpCsFixer\Finder::create()
    ->in(__DIR__)
    ->exclude('node_modules/')
    ->exclude('storage/framework/')
    ->exclude('vendor/')
    ->notPath('c3.php');

$config = new PhpCsFixer\Config();

return $config
    ->setIndent('    ')
    ->setLineEnding("\n")
    ->setFinder($finder)
    ->setRules([
        '@PSR12' => true,
        '@PHP80Migration' => true,
        'array_push' => true,
        'binary_operator_spaces' => true,
        'blank_line_before_statement' => true,
        'cast_spaces' => true,
        'class_attributes_separation' => [
            'elements' => [
                'const' => 'one',
                'method' => 'one',
                'property' => 'only_if_meta',
                'trait_import' => 'none',
            ],
        ],
        'concat_space' => ['spacing' => 'one'],
        'constant_case' => true,
        'declare_strict_types' => true,
        'echo_tag_syntax' => true,
        'function_typehint_space' => true,
        'linebreak_after_opening_tag' => true,
        'logical_operators' => true,
        'method_argument_space' => [
            'after_heredoc' => true,
            'on_multiline' => 'ensure_fully_multiline',
        ],
        'modernize_types_casting' => true,
        'multiline_whitespace_before_semicolons' => true,
        'native_function_casing' => true,
        'no_blank_lines_after_phpdoc' => true,
        'no_empty_comment' => true,
        'no_empty_phpdoc' => true,
        'no_empty_statement' => true,
        'no_extra_blank_lines' => true,
        'no_leading_namespace_whitespace' => true,
        'no_multiline_whitespace_around_double_arrow' => true,
        'no_php4_constructor' => true,
        'no_short_bool_cast' => true,
        'no_singleline_whitespace_before_semicolons' => true,
        'no_spaces_around_offset' => true,
        'no_superfluous_elseif' => true,
        'no_trailing_comma_in_list_call' => true,
        'no_trailing_comma_in_singleline_array' => true,
        'no_unused_imports' => true,
        'no_useless_else' => true,
        'no_useless_return' => true,
        'no_whitespace_before_comma_in_array' => [
            'after_heredoc' => true,
        ],
        'ordered_imports' => [
            'imports_order' => [
                'class',
                'const',
                'function',
            ],
            'sort_algorithm' => 'alpha',
        ],
        'ordered_traits' => true,
        'phpdoc_annotation_without_dot' => true,
        'phpdoc_indent' => true,
        'phpdoc_scalar' => true,
        'phpdoc_separation' => true,
        'phpdoc_single_line_var_spacing' => true,
        'phpdoc_trim_consecutive_blank_line_separation' => true,
        'psr_autoloading' => true,
        'random_api_migration' => true,
        'self_accessor' => true,
        'semicolon_after_instruction' => true,
        'single_line_comment_style' => ['comment_types' => ['hash']],
        'single_quote' => true,
        'standardize_not_equals' => true,
        'strict_comparison' => true,
        'trailing_comma_in_multiline' => [
            'after_heredoc' => true,
            'elements' => [
                'arrays',
            ],
        ],
        'trim_array_spaces' => true,
        'unary_operator_spaces' => true,
        'whitespace_after_comma_in_array' => true,
    ]);
