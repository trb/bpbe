$(document).ready(function() {
    var tab_replacement = '    ';
    /*
     * Record wether shift is pressed or not (shift+tab should remove
     * indentation). Don't mix with the keydown-event handler further down
     * for readability and clarity.
     */
    var shift_pressed = false;
    $('#article-text').keydown(function(event) {
        if (event.which === 16) {
            shift_pressed = true;
        }
    });
    $('#article-text').keyup(function(event) {
        if (event.which === 16) {
            shift_pressed = false;
        }
    });
    
    /*
     * Keycode 9 == tab key, insert 4 spaces
     */
    $('#article-text').keydown(function(event) {
        /*
         * Kills event. After a call to this function, no handler will be
         * triggered.
         */
        function stop(event) {
            event.stopImmediatePropagation();
            event.stopPropagation();
            event.preventDefault();
        }
        
        function get_text() {
            return $('#article-text').val();
        }
        
        function set_text(text) {
            $('#article-text').val(text);
        }
        
        function insert(index, text) {
            if (typeof index !== 'number') {
                throw 'Index must be specified by a number';
            }
            
            var field = $('#article-text');
            var value = get_text();
            
            value = value.substring(0, index) + text + value.substring(index);
            
            set_text(value);
            
            field.setSelection(index + text.length, index + text.length);
        }
        
        function get_selection() {
            return $('#article-text').getSelection();
        }
        
        /**
         * Find the first newline before position 'index' in 'text'. If no
         * previous newline is found, 0 will be returned (start of text)
         * 
         * @param int index - Everything up to this position is searched
         * @param string text - Text to search
         */
        function find_previous_newline(index, text) {
            var start = index;
            /*
             * If the selections starts with a newline, the caret
             * is position at the end of the previous line. The
             * character before the current newline is the last
             * character of the previous line, so start with that
             * character.
             */
            if ((text[start] === '\n') && (start > 0)) {
                --start;
            }
            for (; (text[start] != '\n') && (start > 0); --start) {
            }
            return start;
        }
        
        function indent_line(selection) {
            insert(selection.start, tab_replacement);
        }
        
        function unindent_line(selection, text) {
            var look_from = find_previous_newline(selection.start, text);
            /*
             * Skip newline if newline is the current
             * character, so that substring() will not cut it
             * from the text.
             */
            if (look_from > 0) {
                ++look_from;
            }
            
            /*
             * Only if the line is indented (newline is
             * followed by tab_replacement), remove
             * intendation.
             */
            if (text.substring(look_from, look_from + tab_replacement.length)
                    == tab_replacement)
            {
                var prefix = text.substring(0, look_from);
                var postfix = text.substring(look_from+tab_replacement.length);
                
                text = prefix + postfix;
                
                set_text(text);
                
                /*
                 * If caret was more than tab_replacement.length
                 * characters into the line, subtracting the
                 * length of tab_replacement from the old position
                 * keeps the caret at the same relative position.
                 * 
                 * But if the caret was positioned in the
                 * tab_replacement.length characters following
                 * the newline, removing tab_replacement.length
                 * would position the caret in the previous line,
                 * so simply set it to the beginning of the line (look_from)
                 */
                if ((selection.start - look_from) > tab_replacement.length) {
                    var new_caret_position = selection.start
                                              - tab_replacement.length;
                } else {
                    var new_caret_position = look_from;
                }
                
                if (new_caret_position < 0) {
                    new_caret_position = 0;
                }
                
                $('#article-text').setSelection(new_caret_position,
                                                new_caret_position);
            }
        }
        
        function handle_indentation_line(selection, text) {
            
            /*
             * If shift is pressed, one level of indentation should
             * be removed:
             * 
             * Find previous newline, check if tab_replacement
             * follows it and if so, remove tab_replacement
             */
            if (shift_pressed) {
                unindent_line(selection, text);
            } else {
                indent_line(selection);
            }
        }
        
        function handle_indentation_block(selection, text) {
            var start = selection.start;
            var end = selection.end;
            
            /*
             * Marking up to a line end indicates that a user wants
             * the line before the line end indented, too
             */
            if ((text[start] == '\n') && (start > 0)) {
                --start;
            }
            while ((text[start] != '\n') && (start > 0)) {
                --start;
            }
            
            while ((text[end] != '\n') && (end < text.length)) {
                ++end;
            }
            
            var prefix = text.substring(0, start);
            var postfix = text.substring(end);
            var text = text.substring(start, end);
            
            if (shift_pressed) {
                var regex = new RegExp('\n' + tab_replacement, 'g');
                var replacement = '\n';
            } else {
                var regex = new RegExp('\n', 'g');
                var replacement = '\n' + tab_replacement;
            }
            
            /*
             * Empty prefix means the first line is selected and therefore,
             * should be indented, too.
             */
            if (prefix === '') {
                if (shift_pressed) {
                    if (text.substring(0, tab_replacement.length)
                        === tab_replacement)
                    {
                        text = text.substring(tab_replacement.length);
                    }
                } else {
                    text = tab_replacement + text;
                }
            }
            
            if (text.match(regex) === null) {
                return; //No line to indent marked
            }
            
            var new_text = text.replace(regex, replacement);
            
            var characters_changed = new_text.length - text.length;
            
            text = prefix + new_text + postfix;
            
            set_text(text);
            
            var selection_start = selection.start;
            var selection_end = selection.end + characters_changed;
                
            while ((text[selection_end] != '\n')
                    && (selection_end < text.length))
            {
                ++selection_end;
            }
            
            if (start === 0) {
                selection_start = 0;
            } else {
                selection_start = start+1;
            }
            
            $('#article-text').setSelection(selection_start, selection_end);
        }
        
        switch (event.which) {
            //9 is the code for the tab-key
            case 9:
                stop(event);
                
                var selection = get_selection();
                var text = get_text();
                /*
                 * A normal caret is representation with start==end on the
                 * selection object. For a real selection, those values
                 * differ, so use that to differentiate indentation methods.
                 */
                if (selection.start === selection.end) {
                    handle_indentation_line(selection, text);
                } else {
                    handle_indentation_block(selection, text);
                }
            break;
            
            //13 is the code for the enter-key
            case 13:
                stop(event);
                
                var selection = get_selection();
                var text = get_text();
                
                var index = find_previous_newline(selection.start, text);
                var text = text.substring(index+1);
                
                var regex = new RegExp('^(' + tab_replacement + ')+');
                
                var spaces = text.match(regex);
                
                if (spaces === null) {
                    var prefix = '';
                } else {
                    /*
                     * Contains however often tab_replacement was repeated
                     * at the front of the line
                     */
                    var prefix = spaces[0];
                }
                
                /*
                 * @todo:
                 * 
                 * Check current line for indendation (whitespace in
                 * beginning is > 0  and % 4 == 0), if there is some
                 * insert the same indendation after newline
                 */
                insert(selection.start, '\n' + prefix);
        }
        
        $('#article_text').trigger('edited', event);
    });
    
    $('#article_text').keyup(function(event) {
        $('#article_text').trigger('edited', event);
    });
    
    
    $('#article_text').bind('edited', function(event) {
        var input = $('#article_text').val();
        
        var converter = Markdown.getSanitizingConverter();
        
        var html = converter.makeHtml(input);
        
        $('#article_preview').html(html);
        
        
        $('article code').each(function(i, element) {
            window.hljs.highlightBlock(element);
        });
    });
});