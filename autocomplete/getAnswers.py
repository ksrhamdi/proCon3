# Import external modules
from google.appengine.ext import ndb
import json
import logging
import os
import webapp2
# Import app modules
from configAutocomplete import const as conf
import answer
import answerVote
import httpServer
import httpServerAutocomplete
import linkKey
import question
import user


class QuestionAnswersForPrefix( webapp2.RequestHandler ):
    def get( self, linkKeyStr, questionId ):

        logging.debug( 'QuestionAnswersForPrefix.get() linkKeyStr=' + str(linkKeyStr) + ' questionId=' + str(questionId) )

        # Collect inputs.
        answerStart = self.request.get( 'answerStart', None )
        logging.debug( 'QuestionAnswersForPrefix.get() answerStart=' + str(answerStart) )

        httpRequestId = os.environ.get( conf.REQUEST_LOG_ID )
        responseData = { 'success':False, 'httpRequestId':httpRequestId }
        
        # Retrieve and check linkKey.
        linkKeyRecord = linkKey.LinkKey.get_by_id( linkKeyStr )
        if (linkKeyRecord is None) or (linkKeyRecord.destinationType != conf.SURVEY_CLASS_NAME):
            httpServer.outputJsonError( conf.BAD_LINK, responseData, self.response );  return;
        surveyId = linkKeyRecord.destinationId
        userId = user.getCookieId( self.request, loginRequired=linkKeyRecord.loginRequired )

        # Check that question is part of survey, because the answer query may be too expensive to allow unnecessary calls.
        questionRecord = question.Question.get_by_id( int(questionId) )
        if questionRecord is None:  httpServer.outputJsonError( 'questionRecord is null', responseData, self.response );  return;
        if questionRecord.surveyId != surveyId:  httpServer.outputJsonError( 'questionRecord.surveyId != surveyId', responseData, self.response );  return;

        # Retrieve best suggested answers for this question and creator.
        answersOrdered = answer.retrieveTopAnswersAsync( surveyId, questionId, answerStart=answerStart )
        logging.debug( 'QuestionAnswersForPrefix.get() answersOrdered=' + str(answersOrdered) )

        answerDisplays = [ httpServerAutocomplete.answerToDisplay(a, userId) for a in answersOrdered ]

        # Display answers data.
        responseData.update(  { 'success':True , 'answers':answerDisplays }  )
        self.response.out.write( json.dumps( responseData ) )


class UserAnswer( webapp2.RequestHandler ):
    def get( self, linkKeyStr, questionId ):

        logging.debug( 'UserAnswer.get() linkKeyStr=' + linkKeyStr )

        # Collect inputs.
        httpRequestId = os.environ.get( conf.REQUEST_LOG_ID )
        responseData = { 'success':False, 'httpRequestId':httpRequestId }
        
        # Retrieve and check linkKey.
        linkKeyRecord = linkKey.LinkKey.get_by_id( linkKeyStr )
        if (linkKeyRecord is None) or (linkKeyRecord.destinationType != conf.SURVEY_CLASS_NAME):
            httpServer.outputJsonError( conf.BAD_LINK, responseData, self.response );  return;
        surveyId = linkKeyRecord.destinationId
        userId = user.getCookieId( self.request, loginRequired=linkKeyRecord.loginRequired )

        # Retrieve all answers for this question and voter
        answerVoteRec = answerVote.get( questionId, userId )
        logging.debug( 'UserAnswer.get() answerVoteRec=' + str(answerVoteRec) )
        
        answerRecord = answer.Answer.get_by_id( answerVoteRec.answerId )
        logging.debug( 'UserAnswer.get() answerRecord=' + str(answerRecord) )

        if answerRecord.surveyId != surveyId:  httpServer.outputJsonError( 'answerRecord.surveyId != surveyId', responseData, self.response );  return;

        answerDisplay = httpServerAutocomplete.answerToDisplay( answerRecord, userId ) if answerRecord  else None

        # Display answers data.
        responseData.update(  { 'success':True , 'answer':answerDisplay }  )
        self.response.out.write( json.dumps( responseData ) )


class UserAnswers( webapp2.RequestHandler ):
    def get( self, linkKeyStr ):

        logging.debug( 'UserAnswers.get() linkKeyStr=' + linkKeyStr )

        # Collect inputs.
        httpRequestId = os.environ.get( conf.REQUEST_LOG_ID )
        responseData = { 'success':False, 'httpRequestId':httpRequestId }
        
        # Retrieve and check linkKey.
        linkKeyRecord = linkKey.LinkKey.get_by_id( linkKeyStr )
        if (linkKeyRecord is None) or (linkKeyRecord.destinationType != conf.SURVEY_CLASS_NAME):
            httpServer.outputJsonError( conf.BAD_LINK, responseData, self.response );  return;
        surveyId = linkKeyRecord.destinationId
        userId = user.getCookieId( self.request, loginRequired=linkKeyRecord.loginRequired )

        # Retrieve all answers for this survey and voter
        answerVoteRecs = answerVote.AnswerVote.query( answerVote.AnswerVote.surveyId==surveyId, answerVote.AnswerVote.userId==userId ).fetch()
        logging.debug( 'UserAnswers.get() answerVoteRecs=' + str(answerVoteRecs) )
        
        answerRecordKeys = [ ndb.Key( answer.Answer, a.answerId )  for a in answerVoteRecs  if (a is not None) and (a.answerId is not None) ]
        answerRecords = ndb.get_multi( answerRecordKeys )
        logging.debug( 'UserAnswers.get() answerRecords=' + str(answerRecords) )
        
        answerIdToContent = { a.key.id() : a.content  for a in answerRecords }
        questionIdToAnswerContent = { v.questionId : answerIdToContent.get( v.answerId, None )  for v in answerVoteRecs }

        # Display answers data.
        responseData.update(  { 'success':True , 'questionIdToAnswerContent':questionIdToAnswerContent }  )
        self.response.out.write( json.dumps( responseData ) )


class QuestionAnswersFromCreator( webapp2.RequestHandler ):
    def get( self, linkKeyStr, questionId ):

        logging.debug( 'QuestionAnswersFromCreator.get() linkKeyStr=' + str(linkKeyStr) + ' questionId=' + str(questionId) )

        # Collect inputs.
        httpRequestId = os.environ.get( conf.REQUEST_LOG_ID )
        responseData = { 'success':False, 'httpRequestId':httpRequestId }
        
        # Retrieve and check linkKey.
        linkKeyRecord = linkKey.LinkKey.get_by_id( linkKeyStr )
        if (linkKeyRecord is None) or (linkKeyRecord.destinationType != conf.SURVEY_CLASS_NAME):
            httpServer.outputJsonError( conf.BAD_LINK, responseData, self.response );  return;
        surveyId = linkKeyRecord.destinationId
        userId = user.getCookieId( self.request, loginRequired=linkKeyRecord.loginRequired )

        # Retrieve all answers for this question and creator.
        answerRecords = answer.Answer.query( answer.Answer.questionId==questionId, answer.Answer.creator==userId ).fetch()
        answersByContent = sorted( answerRecords, key=lambda a:a.content )
        answerDisplays = [ httpServerAutocomplete.answerToDisplay(a, userId) for a in answersByContent ]

        # Display answers data.
        responseData = { 'success':True , 'answers':answerDisplays }
        self.response.out.write( json.dumps( responseData ) )


class QuestionFrequentAnswers( webapp2.RequestHandler ):
    def get( self, linkKeyStr, questionId ):

        logging.debug( 'QuestionFrequentAnswers.get() linkKeyStr=' + str(linkKeyStr) + ' questionId=' + str(questionId) )

        # Collect inputs.
        answerStart = self.request.get( 'answerStart', None )
        logging.debug( 'QuestionFrequentAnswers.get() answerStart=' + str(answerStart) )
        all = ( self.request.get( 'all', None ) == 'true' )

        httpRequestId = os.environ.get( conf.REQUEST_LOG_ID )
        responseData = { 'success':False, 'httpRequestId':httpRequestId }
        
        # Retrieve and check linkKey.
        linkKeyRecord = linkKey.LinkKey.get_by_id( linkKeyStr )
        if (linkKeyRecord is None) or (linkKeyRecord.destinationType != conf.SURVEY_CLASS_NAME):  httpServer.outputJsonError( conf.BAD_LINK, responseData, self.response );  return;
        surveyId = linkKeyRecord.destinationId
        userId = user.getCookieId( self.request, loginRequired=linkKeyRecord.loginRequired )
        
        # Check that question is part of survey, because the answer query may be too expensive to allow unnecessary calls.
        questionRecord = question.Question.get_by_id( int(questionId) )
        if questionRecord is None:  httpServer.outputJsonError( 'questionRecord is null', responseData, self.response );  return;
        if questionRecord.surveyId != surveyId:  httpServer.outputJsonError( 'questionRecord.surveyId != surveyId', responseData, self.response );  return;

        # Retrieve most frequent answers for question
        if all:
            answerRecordsTrunc = answer.Answer.query( answer.Answer.surveyId==surveyId, answer.Answer.questionId==questionId, answer.Answer.voteCount > 0 
                ).order( -answer.Answer.voteCount ).fetch()
            hasMoreAnswers = False

        else:
            maxAnswersPerQuestion = 5
            answerRecords = answer.Answer.query( answer.Answer.surveyId==surveyId, answer.Answer.questionId==questionId, answer.Answer.voteCount > 0 
                ).order( -answer.Answer.voteCount ).fetch( maxAnswersPerQuestion + 1 )

            answerRecordsTrunc = answerRecords[ 0 : maxAnswersPerQuestion ]
            hasMoreAnswers = len(answerRecordsTrunc) < len(answerRecords)

        logging.debug( 'QuestionFrequentAnswers.get() answerRecordsTrunc=' + str(answerRecordsTrunc) )

        answerDisplays = [ httpServerAutocomplete.answerToDisplay(a, userId) for a in answerRecordsTrunc ]

        # Display answers data.
        responseData.update(  { 'success':True , 'answers':answerDisplays , 'hasMoreAnswers':hasMoreAnswers }  )
        self.response.out.write( json.dumps( responseData ) )



# Route HTTP request
app = webapp2.WSGIApplication( [
    ( r'/autocomplete/getQuestionAnswersForPrefix/([0-9A-Za-z]+)/(\d+)' , QuestionAnswersForPrefix ) ,
    ( r'/autocomplete/getUserAnswer/([0-9A-Za-z]+)' , UserAnswer ) ,
    ( r'/autocomplete/getUserAnswers/([0-9A-Za-z]+)' , UserAnswers ) ,
    ( r'/autocomplete/getQuestionAnswersFromCreator/([0-9A-Za-z]+)/(\d+)' , QuestionAnswersFromCreator ) ,
    ( r'/autocomplete/getQuestionFrequentAnswers/([0-9A-Za-z]+)/(\d+)' , QuestionFrequentAnswers )
] )


