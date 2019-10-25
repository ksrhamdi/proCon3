# Client can delete any unsaved duplicate input, because it will either have no answerId,
# or it will have an older saved answer id/content.


# Import external modules
from google.appengine.ext import ndb
import json
import logging
import os
import webapp2
# Import app modules
import answer
from configAutocomplete import const as conf
import httpServer
import httpServerAutocomplete
import linkKey
import question
import survey
import text
import user



# Returns surveyId, loginRequired from linkKey record, or None
def retrieveSurveyIdFromLinkKey( linkKeyString, responseData, httpResponse ):
    # Retrieve link-key
    linkKeyRec = linkKey.LinkKey.get_by_id( linkKeyString )
    logging.debug( 'retrieveSurveyIdFromLinkKey() linkKeyRec=' + str(linkKeyRec) )

    if linkKeyRec is None:  httpServer.outputJsonError( 'linkKey not found', responseData, httpResponse );  return None, None;
    if linkKeyRec.destinationType != conf.SURVEY_CLASS_NAME:  httpServer.outputJsonError( 'linkKey destinationType=' + str(linkKeyRec.destinationType), responseData, httpResponse );  return None, None;
    return linkKeyRec.destinationId, linkKeyRec.loginRequired


class EditAnswer(webapp2.RequestHandler):

    def post(self):
        logging.debug( 'EditAnswer.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        inputData = json.loads( self.request.body )
        logging.debug( 'EditAnswer.post() inputData=' + str(inputData) )

        content = answer.standardizeContent( text.formTextToStored( inputData['content'] ) )
        linkKeyString = inputData['linkKey']
        answerId = inputData['answerId']
        questionId = str( int( inputData['questionId'] ) )
        browserCrumb = inputData.get( 'crumb', None )
        loginCrumb = inputData.get( 'crumbForLogin', None )
        logging.debug( 'EditAnswer.post() content=' + str(content) + ' browserCrumb=' + str(browserCrumb) 
            + ' loginCrumb=' + str(loginCrumb) 
            + ' linkKeyString=' + str(linkKeyString) + ' answerId=' + str(answerId) )

        responseData = { 'success':False, 'requestLogId':requestLogId }

        surveyId, loginRequired = retrieveSurveyIdFromLinkKey( linkKeyString, responseData, self.response )
        if surveyId is None:  return

        # User id from cookie, crumb...
        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=loginRequired, loginCrumb=loginCrumb )
        if userId is None: return
        
        # Retrieve survey record to check survey creator
        surveyRec = survey.Survey.get_by_id( int(surveyId) )
        if surveyRec is None:  httpServer.outputJsonError( 'survey record not found', responseData, self.response );  return None;
        if surveyRec.creator != userId:  httpServer.outputJsonError( 'surveyRec.creator != userId', responseData, self.response );  return None;
      
        # Split answers by newline
        contentLines = content.split( '\n' )  if content  else []
        # For each non-empty answer...
        answerDisplays = []
        for contentLine in contentLines:
            logging.debug( 'EditAnswer.post() contentLine=' + str(contentLine) )
            if not contentLine:  continue

            # Check answer length
            if not httpServer.isLengthOk( contentLine, '', conf.minLengthAnswer ):
                httpServer.outputJsonError( conf.TOO_SHORT, responseData, self.response )
                return

            # If new answer value already exists... error.  If new answer is same as old answer value... no problem?
            newAnswerId = answer.toKeyId( questionId, contentLine )
            answerRec = answer.Answer.get_by_id( newAnswerId )
            if answerRec:  continue

            # Delete old answer
            if answerId:
                oldAnswerRec = answer.Answer.get_by_id( answerId )
                if oldAnswerRec is None:  httpServer.outputJsonError( 'answer record not found', responseData, self.response );  return;
                if oldAnswerRec.surveyId != surveyId:  httpServer.outputJsonError( 'oldAnswerRec.surveyId != surveyId', responseData, self.response );  return;
                oldAnswerRec.key.delete()
            # Create new answer
            answerRec = answer.newAnswer( questionId, surveyId, contentLine, userId, voteCount=0 )
            answerDisplay = httpServerAutocomplete.answerToDisplay( answerRec, userId )
            answerDisplays.append( answerDisplay )
        
        # Display updated answers
        responseData.update(  { 'success':True, 'answers':answerDisplays }  )
        self.response.out.write( json.dumps( responseData ) )



class DeleteAnswer(webapp2.RequestHandler):

    def post(self):
        logging.debug( 'DeleteAnswer.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        inputData = json.loads( self.request.body )
        logging.debug( 'DeleteAnswer.post() inputData=' + str(inputData) )

        linkKeyString = inputData['linkKey']
        answerId = inputData['answerId']
        browserCrumb = inputData.get( 'crumb', None )
        loginCrumb = inputData.get( 'crumbForLogin', None )
        logging.debug( 'DeleteAnswer.post() browserCrumb=' + str(browserCrumb) 
            + ' loginCrumb=' + str(loginCrumb) 
            + ' linkKeyString=' + str(linkKeyString) + ' answerId=' + str(answerId) )

        responseData = { 'success':False, 'requestLogId':requestLogId }

        surveyId, loginRequired = retrieveSurveyIdFromLinkKey( linkKeyString, responseData, self.response )
        if surveyId is None:  return

        # User id from cookie, crumb...
        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=loginRequired, loginCrumb=loginCrumb )
        if userId is None: return

        # Retrieve survey record to check survey creator
        surveyRec = survey.Survey.get_by_id( int(surveyId) )
        if surveyRec is None:  httpServer.outputJsonError( 'survey record not found', responseData, self.response );  return None;
        if surveyRec.creator != userId:  httpServer.outputJsonError( 'surveyRec.creator != userId', responseData, self.response );  return None;

        # Delete old answer.
        if answerId:
            oldAnswerRec = answer.Answer.get_by_id( answerId )
            if oldAnswerRec is None:  httpServer.outputJsonError( 'answer record not found', responseData, self.response );  return;
            if oldAnswerRec.surveyId != surveyId:  httpServer.outputJsonError( 'oldAnswerRec.surveyId != surveyId', responseData, self.response );  return;
            oldAnswerRec.key.delete()
        
        # Display result.
        responseData.update(  { 'success':True }  )
        self.response.out.write( json.dumps( responseData ) )



class SetAnswer(webapp2.RequestHandler):

    def post(self):
        logging.debug( 'SetAnswer.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        inputData = json.loads( self.request.body )
        logging.debug( 'SetAnswer.post() inputData=' + str(inputData) )

        content = answer.standardizeContent( inputData.get( 'content', None ) )
        linkKeyString = inputData['linkKey']
        questionId = str( int( inputData['questionId'] ) )
        browserCrumb = inputData.get( 'crumb', None )
        loginCrumb = inputData.get( 'crumbForLogin', None )
        logging.debug( 'SetAnswer.post() content=' + str(content) + ' browserCrumb=' + str(browserCrumb) 
            + ' loginCrumb=' + str(loginCrumb) 
            + ' linkKeyString=' + str(linkKeyString) )

        responseData = { 'success':False, 'requestLogId':requestLogId }

        surveyId, loginRequired = retrieveSurveyIdFromLinkKey( linkKeyString, responseData, self.response )
        if surveyId is None:  return

        # User id from cookie, crumb...
        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=loginRequired, loginCrumb=loginCrumb )
        if userId is None: return

        # Check answer length
        if ( content is not None ) and not httpServer.isLengthOk( content, '', conf.minLengthAnswer ):
            httpServer.outputJsonError( conf.TOO_SHORT, responseData, self.response )
            return

        # Retrieve question record.
        questionRec = question.Question.get_by_id( int(questionId) )
        logging.debug( 'SetAnswer.post() questionRec=' + str(questionRec) )

        if questionRec is None:  httpServer.outputJsonError( 'question not found', responseData, self.response );  return;
        if questionRec.surveyId != surveyId:  httpServer.outputJsonError( 'questionRec.surveyId != surveyId', responseData, self.response );  return;
        
        # Update answer and vote.
        answerRec, voteRecord = answer.vote( questionId, surveyId, content, userId, questionRec.creator )

        # Display updated answer.
        responseData.update(  { 'success':True, 'answerContent':content }  )
        self.response.out.write( json.dumps( responseData ) )



# Route HTTP request
app = webapp2.WSGIApplication([
    ('/autocomplete/editAnswer', EditAnswer),
    ('/autocomplete/deleteAnswer', DeleteAnswer),
    ('/autocomplete/setAnswer', SetAnswer)
])


