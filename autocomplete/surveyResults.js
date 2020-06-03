
/////////////////////////////////////////////////////////////////////////////////
// Question results

        function
    QuestionResultDisplay( questionId ){
        // User-interface state variables (not persistent data)
        ElementWrap.call( this );  // Inherit member data from ElementWrap.

        this.createFromHtml( questionId, '\n\n' + [
            '<h1 class=title id=title> Question Results </h1>',
            '<div class=Question id=Question>',
            '    <div id=Message role=alert></div>',
            '    <label for=QuestionContent id=QuestionPosition></label>',
            '    <div class=QuestionContent id=QuestionContent></div>',
            '    <div class=Answers id=Answers></div>',
            '    <button class=QuestionResultsButton id=QuestionResultsButton onclick=onQuestionResultsClick> More answers </button>',
            '</div>'
        ].join('\n') );
    }
    QuestionResultDisplay.prototype = Object.create( ElementWrap.prototype );  // Inherit methods from ElementWrap.

    // Set all data.
        QuestionResultDisplay.prototype.
    setAllData = function( questionData, topDisp ){
        this.question = questionData;
        this.answers = [ ];
        this.topDisp = topDisp;
        this.dataUpdated();

        // Retrieve frequent answers, async
        this.retrieveAnswers();
    };
    
    // Update html from data.
        QuestionResultDisplay.prototype.
    dataUpdated = function( ){

        this.message = showMessageStruct( this.message, this.getSubElement('Message') );
        
        this.setInnerHtml( 'QuestionContent', this.question.content );
        if ( ! this.singleQuestionPage ){
            this.setInnerHtml( 'QuestionPosition', 'Question ' + (this.question.positionInSurvey + 1) );
            this.setStyle( 'QuestionResultsButton', 'display', (this.hasMoreAnswers ? 'inline-block' : null) );
            this.setStyle( 'title', 'display', 'none' );
        }

        // Group answers by answer-without-reason
        var answerToData = {};
        for ( var r = 0;  r < this.answers.length;  ++r ) { 
            var answerData = this.answers[r];
            if ( ! answerData ){  continue;  }
            var answerAndReasonArray = parseAnswerAndReason( answerData.content );
            if ( ! answerAndReasonArray ){  continue;  }
            var answerText = answerAndReasonArray[0];
            var reasonText = answerAndReasonArray[1];
            if ( ! (answerText in answerToData) ){  
                answerToData[ answerText ] = { answerText:answerText, answerCount:0, reasons:[] };  
            }
            var answerGroupData = answerToData[ answerText ];
            answerGroupData.answerCount += answerData.voteCount;
            answerGroupData.reasons.push( answerData );
        }

        // Order answers by total vote-count
        var answerTextByTotalVote = [];
        for ( var answerText in answerToData ){  answerTextByTotalVote.push( answerText );  }
        answerTextByTotalVote.sort(  function(a,b){ return (answerToData[b].answerCount - answerToData[a].answerCount); }  );

        // For each answer (ignoring reasons) ...
        var answersDiv = this.getSubElement('Answers');
        clearChildren( answersDiv );
        var sumQuestionVotes = this.answers.reduce(  function(agg, ans){ return agg + ans.voteCount; } , 0  );
        for ( var a = 0;  a < answerTextByTotalVote.length;  ++a ){
            var answerText = answerTextByTotalVote[a];
            var answerGroupData = answerToData[ answerText ];
            var sumAnswerVotes = answerGroupData.reasons.reduce(  function(agg, r){ return agg + r.voteCount; } , 0  );

            var voteFrac = sumAnswerVotes / sumQuestionVotes;
            var opacityFrac = (voteFrac * 1.5) + 0.25;

            // Build answer-without-reason table-row
            // Use html-builder instead of text-to-html which fails on partial table
            var answerDiv = html('tr').class('Answer').children( 
                html('td').class('AnswerCell').class('AnswerCountBarBack').children(
                    html('div').class('AnswerCountBar').style('width', parseInt(voteFrac * 100) + '%').innerHtml('&nbsp;').build()
                ).build() ,
                html('td').class('AnswerCell').class('AnswerCount').innerHtml(sumAnswerVotes).build() ,
                html('td').class('AnswerCell').class('AnswerContent').style('opacity', opacityFrac).innerHtml(answerGroupData.answerText).build()
            ).build();
            answersDiv.appendChild( answerDiv );

            // Build answers-with-reasons expander
            // Use separate table for answers-with-reasons, because expander cannot work on just some table-rows
            var reasonsDiv = html('div').class('AnswerReasons').build();
            var expandableRow = html('tr').children(
                html('td').attribute('colspan', 3).children(
                    html('details').attribute('open', 'open').children(
                        html('summary').innerHtml('&nbsp;').build() ,
                        reasonsDiv
                    ).build()
                ).build()
            ).build();
            answersDiv.appendChild( expandableRow );

            // For each answer-reason...
            for ( var r = 0;  r < answerGroupData.reasons.length;  ++r ){
                var reasonData = answerGroupData.reasons[r];
                var answerAndReasonArray = parseAnswerAndReason( reasonData.content );
                var reasonText = answerAndReasonArray[1];

                // Build table-row
                voteFrac = reasonData.voteCount / sumAnswerVotes;
                opacityFrac = (voteFrac * 1.5) + 0.25;
                reasonsDiv.appendChild(  htmlToElement( '\n' + [
                    '       <div class=AnswerReason>' ,
                    '           <div class="AnswerCell AnswerCountBarBack"></div>' ,
                    '           <div class="AnswerCell AnswerCount">' + reasonData.voteCount + '</div>' ,
                    '           <div class="AnswerCell AnswerContent" style="opacity:' + opacityFrac + ';">' + reasonText + '</div>' ,
                    '       </div>'
                ].join('\n') )  );
            }
        }

    };

        QuestionResultDisplay.prototype.
    onQuestionResultsClick = function( ){
        setFragmentFields( {page:FRAG_PAGE_QUESTION_RESULTS, question:this.question.id} );
    };


    // For use by single-question results page
        QuestionResultDisplay.prototype.
    retrieveData = function( ){

        // request via ajax
        var thisCopy = this;
        var sendData = { };
        var url = '/autocomplete/getQuestion/' + this.topDisp.linkKey.id + '/' + this.question.id;
        ajaxGet( sendData, url, function(error, status, receiveData){
            if ( receiveData ){
                if ( receiveData.success ){
                    thisCopy.linkOk = true;
                    if ( receiveData.question ){
                        // Update question fields
                        thisCopy.question.content = receiveData.question.content;
                    }
                    thisCopy.dataUpdated();
                }
            }
        } );
    };
    
        QuestionResultDisplay.prototype.
    retrieveAnswers = function( ){

        // request via ajax
        var thisCopy = this;
        var sendData = { };
        var url = '/autocomplete/getQuestionFrequentAnswers/' + this.topDisp.linkKey.id + '/' + this.question.id;
        if ( this.singleQuestionPage ){  url += '?all=true';  }
        ajaxGet( sendData, url, function(error, status, receiveData){
            if ( receiveData ){
                if ( receiveData.success ){
                    // Update answer data
                    if ( receiveData.answers ){
                        thisCopy.answers = receiveData.answers;
                        thisCopy.hasMoreAnswers = receiveData.hasMoreAnswers;
                        thisCopy.dataUpdated();
                    }
                }
                else {
                    thisCopy.message = { color:RED, text:'Could not retrieve answers' };
                    thisCopy.dataUpdated();
                }
            }
        } );
    };
    



/////////////////////////////////////////////////////////////////////////////////
// Survey results

        function
    SurveyResultDisplay( surveyId ){
        // User-interface state variables (not persistent data)
        ElementWrap.call( this );  // Inherit member data from ElementWrap.

        this.createFromHtml( surveyId, '\n\n' + [
            '<h1 class=title> Survey Results </h1>',
            '<div class=Survey id=Survey>',
            '    <div id=Message role=alert></div>',
            '    <div class=Questions id=Questions></div>',
            '</div>'
        ].join('\n') );
    }
    SurveyResultDisplay.prototype = Object.create( ElementWrap.prototype );  // Inherit methods from ElementWrap.

    // Set all data.
        SurveyResultDisplay.prototype.
    setAllData = function( surveyData, questionIds, questions, topDisp ){
        // Data passed from caller, so that old cached data can be reused.
        this.survey = surveyData;
        this.questions = questions;
        this.questionIds = questionIds;

        this.topDisp = topDisp;

        this.dataUpdated();
    };
    
    // Update html from data.
        SurveyResultDisplay.prototype.
    dataUpdated = function( ){

        var surveyIntroStart = ( this.survey && this.survey.introduction )?  ': ' + this.survey.introduction.substr(0, 50)  :  '';
        document.title = SITE_TITLE + ': View Survey' + surveyIntroStart;

        this.message = showMessageStruct( this.message, this.getSubElement('Message') );

        // For each question with data, in survey order... ensure question display exists
        for ( var q = 0;  q < this.questionIds.length;  ++q ){
            var questionId = this.questionIds[q];

            var question = this.questions[ questionId ];
            if ( question.data  &&  ! question.display ){
                // Create display
                question.display = new QuestionResultDisplay( question.data.id );
                question.display.setAllData( question.data, this.topDisp );
                // Add to webpage
                var questionsDiv = this.getSubElement('Questions');
                addAndAppear( question.display.element, questionsDiv );
            }
        }
    };
    
        SurveyResultDisplay.prototype.
    retrieveData = function( ){

        // request via ajax
        var thisCopy = this;
        var sendData = { };
        var url = '/autocomplete/getSurvey/' + this.topDisp.linkKey.id;
        ajaxGet( sendData, url, function(error, status, receiveData){
            if ( receiveData ){
                if ( receiveData.success ){
                    thisCopy.linkOk = true;
                    if ( receiveData.survey ){
                        // Update survey fields
                        thisCopy.survey.id = receiveData.survey.id;
                        thisCopy.survey.introduction = receiveData.survey.introduction;
                    }
                    // Retrieve questions data, async
                    thisCopy.retrieveQuestions();
                    thisCopy.dataUpdated();
                }
            }
        } );
    };
    
        SurveyResultDisplay.prototype.
    retrieveQuestions = function( ){

        // request via ajax
        var thisCopy = this;
        var sendData = { };
        var url = '/autocomplete/getSurveyQuestions/' + this.topDisp.linkKey.id;
        ajaxGet( sendData, url, function(error, status, receiveData){
            if ( receiveData ){
                if ( receiveData.success ){
                    thisCopy.linkOk = true;
                    if ( receiveData.questions ){
                        // Update question order
                        thisCopy.questionIds = receiveData.questions.map( q => q.id );
                        // For each received question data... overwrite existing question data
                        for ( var q = 0;  q < receiveData.questions.length;  ++q ){
                            var questionReceived = receiveData.questions[q];
                            var question = thisCopy.questions[ questionReceived.id ];
                            if ( question ){
                                question.data = questionReceived;
                            }
                            else {
                                question = { data:questionReceived };
                                thisCopy.questions[ questionReceived.id ] = question;
                            }
                        }
                    }
                    thisCopy.dataUpdated();
                }
                else if ( receiveData.message == BAD_LINK ){
                    thisCopy.linkOk = false;
                    thisCopy.dataUpdated();
                }
            }
        } );
    };

