/////////////////////////////////////////////////////////////////////////////////
// Constants

    const EDIT = 'edit';
    const TRUE = 'true';
    const FALSE = 'false';
    const ANSWER_TOO_SHORT_MESSAGE = 'Answer is too short'
    const KEY_CODE_ENTER = 13;
    const ANSWER_REASON_DELIMITER = '\t'


/////////////////////////////////////////////////////////////////////////////////
// Global functions

        function
    serializeAnswerAndReason( answer, reason ){
        return (answer || '') + ANSWER_REASON_DELIMITER + (reason || '');
    }

        function
    parseAnswerAndReason( answerAndReasonStr ){
        if ( ! answerAndReasonStr ){  return [ null, null ];  }
        var delimIndex = answerAndReasonStr.indexOf( ANSWER_REASON_DELIMITER );
        if ( delimIndex < 0 ){  return [ answerAndReasonStr, '' ];  }
        return [
            answerAndReasonStr.substr(0, delimIndex),
            answerAndReasonStr.substr(delimIndex + ANSWER_REASON_DELIMITER.length)
        ];
    }

        function
    fitTextAreaToText( textArea ){
        textArea.style.height = '';
        textArea.style.height = textArea.scrollHeight + 'px';
    }


        function 
    addAndAppear( element, parentElement ){  
        var elementJquery = jQuery( element ).hide();
        var parentJquery = jQuery( parentElement ).append( elementJquery );
        elementJquery.slideToggle();
    }


        function
    scrollToHtmlElement( htmlElement ){
        var elementJquery = jQuery( htmlElement );
        jQuery('html, body').animate( {
            scrollTop: $(elementJquery).offset().top + 'px'
        }, 'fast' );
    }


    
        function  // returns series[string]
    storedTextToHtml( storedText ){
        if ( ! storedText ){  return '';  }

        // turn urls into links
        var urlRegex = /(https?:\/\/[^ \n\r\t'"<>]+)/ ;
        var elementIndex = 0;
        var elements = storedText.split( urlRegex );   // series[string]
        elements = elements.map( function(e){  
            if ( e.match(urlRegex) ){  return '<a href="'+e+'" target="_blank" id="'+(elementIndex++)+'">'+e+'</a>';  }
            else {  return e;  }
        } );

        // turn newline into html break  
        var newElements = [ ];
        elements.map( function(e){
            var subElements = e.split( /(\n)/ );
            subElements.map(  function(s){ newElements.push((s == '\n')? '<br id="'+(elementIndex++)+'"/>' : s) }  );
        } );
        elements = newElements;

        // turn tab into 4 spaces  
        elements = elements.map(  function(e){ 
            return e.replace( /\t/g , '    ' );
        } );

        // turn 2spaces into &nbsp;  
        newElements = [ ];
        elements.map( function(e){
            var subElements = e.split( /(  )/ );
            subElements.map(  function(s){ newElements.push((s == '  ')? '<span id='+(elementIndex++)+'">&nbsp;</span>' : s) }  );
        } );

        return newElements.join('');
    }


