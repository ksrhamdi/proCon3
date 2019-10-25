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
import user
import text



class SubmitEditQuestion(webapp2.RequestHandler):

    def post(self):
        logging.debug( 'SubmitEditQuestion.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        inputData = json.loads( self.request.body )
        logging.debug( 'SubmitEditQuestion.post() inputData=' + str(inputData) )

        content = text.formTextToStored( inputData['content'] )
        linkKeyString = inputData['linkKey']
        questionId = inputData.get( 'questionId', None )  # Allow questionId=null, which creates new question
        questionId = str( int(questionId) ) if questionId  else None
        browserCrumb = inputData.get( 'crumb', None )
        loginCrumb = inputData.get( 'crumbForLogin', None )
        logging.debug( 'SubmitEditQuestion.post() content=' + str(content) + ' browserCrumb=' + str(browserCrumb) 
            + ' loginCrumb=' + str(loginCrumb) 
            + ' linkKeyString=' + str(linkKeyString) + ' questionId=' + str(questionId) )

        # Retrieve link-key record
        if linkKeyString is None:  httpServer.outputJsonError( 'linkKeyString is null', responseData, self.response );  return;
        linkKeyRecord = linkKey.LinkKey.get_by_id( linkKeyString )
        logging.debug( 'SubmitEditQuestion.post() linkKeyRecord=' + str(linkKeyRecord) )

        if linkKeyRecord is None:  httpServer.outputJsonError( 'linkKey not found', responseData, self.response );  return;
        if linkKeyRecord.destinationType != conf.SURVEY_CLASS_NAME:  httpServer.outputJsonError( 'linkKey destinationType=' + str(linkKeyRecord.destinationType), responseData, self.response );  return;
        surveyId = linkKeyRecord.destinationId
        loginRequired = linkKeyRecord.loginRequired

        # User id from cookie, crumb...
        responseData = { 'success':False, 'requestLogId':requestLogId }
        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=loginRequired, loginCrumb=loginCrumb )
        if userId is None:  return

        # Check question length
        if not httpServer.isLengthOk( content, '', conf.minLengthQuestion ):
            httpServer.outputJsonError( conf.TOO_SHORT, responseData, self.response )
            return

        # Retrieve survey record
        surveyRec = survey.Survey.get_by_id( int(surveyId) )
        if surveyRec is None:  httpServer.outputJsonError( 'survey not found', responseData, self.response );  return;
        logging.debug( 'SubmitEditQuestion.post() surveyRec=' + str(surveyRec) )
        if userId != surveyRec.creator:  httpServer.outputJsonError( conf.NOT_OWNER, responseData, self.response );  return;

        # Retrieve question record
        # If question record exists...
        if questionId:
            questionRec = question.Question.get_by_id( int(questionId) )
            logging.debug( 'SubmitEditQuestion.post() questionRec=' + str(questionRec) )

            if questionRec is None:  httpServer.outputJsonError( 'question not found', responseData, self.response );  return;
            if questionRec.surveyId != linkKeyRecord.destinationId:  httpServer.outputJsonError( 'questionRec.surveyId != linkKeyRecord.destinationId', responseData, self.response );  return;

            # Verify that question is editable
            if userId != questionRec.creator:  httpServer.outputJsonError( conf.NOT_OWNER, responseData, self.response );  return;
            if not questionRec.allowEdit:  httpServer.outputJsonError( conf.HAS_RESPONSES, responseData, self.response );  return;

            # Update question record.
            questionRec.content = content
            questionRec.put()

        # If question record does not exist...
        else:
            # Create question record
            questionRec = question.Question( surveyId=surveyId, creator=userId, content=content, allowEdit=True )
            questionKey = questionRec.put()
            questionId = str( questionKey.id() )
            
            # Add question id to survey
            # If question is created but survey fails, then question will be orphaned.  Alternatively, use a transaction.
            questionIds = list( surveyRec.questionIds )
            questionIds.append( questionId )
            surveyRec.questionIds = questionIds   # Use property assignment for immediate value checking
            surveyRec.put()
        
        # Display updated question.
        questionDisplay = httpServerAutocomplete.questionToDisplay( questionRec, userId )
        responseData.update(  { 'success':True, 'question':questionDisplay }  )
        self.response.out.write( json.dumps( responseData ) )


class DeleteQuestion(webapp2.RequestHandler):

    def post(self):
        logging.debug( 'DeleteQuestion.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        inputData = json.loads( self.request.body )
        logging.debug( 'DeleteQuestion.post() inputData=' + str(inputData) )

        linkKeyString = inputData['linkKey']
        questionId = inputData['questionId']
        browserCrumb = inputData.get( 'crumb', None )
        loginCrumb = inputData.get( 'crumbForLogin', None )
        logging.debug( 'DeleteQuestion.post() browserCrumb=' + str(browserCrumb) 
            + ' loginCrumb=' + str(loginCrumb) 
            + ' linkKeyString=' + str(linkKeyString) + ' questionId=' + str(questionId) )

        if questionId is None:  httpServer.outputJsonError( 'questionId is null', responseData, self.response );  return;

        # Retrieve link-key record
        if linkKeyString is None:  httpServer.outputJsonError( 'linkKeyString is null', responseData, self.response );  return;
        linkKeyRecord = linkKey.LinkKey.get_by_id( linkKeyString )
        logging.debug( 'DeleteQuestion.post() linkKeyRecord=' + str(linkKeyRecord) )

        if linkKeyRecord is None:  httpServer.outputJsonError( 'linkKey not found', responseData, self.response );  return;
        if linkKeyRecord.destinationType != conf.SURVEY_CLASS_NAME:  httpServer.outputJsonError( 'linkKey destinationType=' + str(linkKeyRecord.destinationType), responseData, self.response );  return;
        surveyId = linkKeyRecord.destinationId
        loginRequired = linkKeyRecord.loginRequired

        # User id from cookie, crumb...
        responseData = { 'success':False, 'requestLogId':requestLogId }
        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=loginRequired, loginCrumb=loginCrumb )
        if userId is None: return

        # Retrieve question and check owner
        questionRec = question.Question.get_by_id( int(questionId) )
        if questionRec is None:  httpServer.outputJsonError( 'question record not found', responseData, self.response );  return;
        if userId != questionRec.creator:  httpServer.outputJsonError( conf.NOT_OWNER, responseData, self.response );  return;

        # Delete question from survey.
        surveyRec = survey.Survey.get_by_id( int(surveyId) )
        logging.debug( 'DeleteQuestion.post() surveyRec=' + str(surveyRec) )
        
        if surveyRec is None:  httpServer.outputJsonError( 'survey record not found', responseData, self.response );  return;
        if userId != surveyRec.creator:  httpServer.outputJsonError( conf.NOT_OWNER, responseData, self.response );  return;

        questionIds = [ q for q in surveyRec.questionIds  if q != questionId ]
        logging.debug( 'DeleteQuestion.post() questionIds=' + str(questionIds) )
        surveyRec.questionIds = questionIds
        surveyRec.put()

        # Delete old question.
        # If fail, question is orphaned, but retrievable by querying by survey id.
        # Using a transaction would be ok, because survey-creator is modifying survey, 
        # which should not be done at the same time as answering, and not done often.
        questionRec.key.delete()

        # Delete answers from question.  If fail, answers are orphaned, but retrievable by querying by question id.
        answerRecords = answer.Answer.query( answer.Answer.questionId==questionId ).fetch()
        logging.debug( 'DeleteQuestion.post() answerRecords=' + str(answerRecords) )
        
        answerKeys = [ a.key  for a in answerRecords ]
        logging.debug( 'DeleteQuestion.post() answerKeys=' + str(answerKeys) )
        
        ndb.delete_multi( answerKeys )
        
        # Display result.
        responseData.update(  { 'success':True }  )
        self.response.out.write( json.dumps( responseData ) )




# Route HTTP request
app = webapp2.WSGIApplication([
    ('/autocomplete/editQuestion', SubmitEditQuestion) ,
    ('/autocomplete/deleteQuestion', DeleteQuestion)
])


