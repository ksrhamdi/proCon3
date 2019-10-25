# Import external modules
from google.appengine.ext import ndb
import json
import logging
import os
import webapp2
# Import app modules
from configAutocomplete import const as conf
import httpServer
import httpServerAutocomplete
import linkKey
import question
import survey
import user
import text



class SubmitNewSurvey( webapp2.RequestHandler ):

    def post(self):
        logging.debug( 'SubmitNewSurvey.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        responseData = { 'success':False, 'requestLogId':requestLogId }
        inputData = json.loads( self.request.body )
        logging.debug( 'SubmitNewSurvey.post() inputData=' + str(inputData) )

        introduction = text.formTextToStored( inputData.get('introduction', '') )
        browserCrumb = inputData.get( 'crumb', '' )
        loginCrumb = inputData.get( 'crumbForLogin', '' )
        loginRequired = inputData.get( 'loginRequired', False )
        logging.debug( 'SubmitNewSurvey.post() introduction=' + str(introduction) + ' browserCrumb=' + str(browserCrumb)
            + ' loginCrumb=' + str(loginCrumb) + ' loginRequired=' + str(loginRequired) )

        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=loginRequired, loginCrumb=loginCrumb )
        if userId is None: return

        # Check survey introduction length.
        if not httpServer.isLengthOk( introduction, '', conf.minLengthSurveyIntro ):  httpServer.outputJsonError( conf.TOO_SHORT, responseData, self.response );  return;
        
        # Construct and store new survey record.
        surveyRecord = survey.Survey( creator=userId, introduction=introduction, allowEdit=True )
        surveyRecordKey = surveyRecord.put()
        logging.debug( 'surveyRecordKey.id={}'.format(surveyRecordKey.id()) )

        # Construct and store link key.
        surveyId = str( surveyRecordKey.id() )
        linkKeyRecord = httpServer.createAndStoreLinkKey( conf.SURVEY_CLASS_NAME, surveyId, loginRequired, self.request, self.response )

        # Display survey.
        surveyDisplay = httpServerAutocomplete.surveyToDisplay( surveyRecord, userId )
        linkKeyDisplay = httpServer.linkKeyToDisplay( linkKeyRecord )
        responseData.update(  { 'success':True, 'linkKey':linkKeyDisplay, 'survey':surveyDisplay }  )
        self.response.out.write( json.dumps( responseData ) )



class SubmitEditSurvey( webapp2.RequestHandler ):

    def post(self):
        logging.debug( 'SubmitEditSurvey.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        inputData = json.loads( self.request.body )
        logging.debug( 'SubmitEditSurvey.post() inputData=' + str(inputData) )

        introduction = text.formTextToStored( inputData['introduction'] )
        linkKeyString = inputData['linkKey']
        browserCrumb = inputData.get( 'crumb', '' )
        loginCrumb = inputData.get( 'crumbForLogin', '' )
        logging.debug( 'SubmitEditSurvey.post() introduction=' + str(introduction) + ' browserCrumb=' + str(browserCrumb) 
            + ' loginCrumb=' + str(loginCrumb) 
            + ' linkKeyString=' + str(linkKeyString) )

        # Retrieve link-key record
        if linkKeyString is None:  httpServer.outputJsonError( 'linkKeyString is null', responseData, self.response );  return;
        linkKeyRecord = linkKey.LinkKey.get_by_id( linkKeyString )
        logging.debug( 'SubmitEditSurvey.post() linkKeyRecord=' + str(linkKeyRecord) )

        if linkKeyRecord is None:  httpServer.outputJsonError( 'linkKey not found', responseData, self.response );  return;
        if linkKeyRecord.destinationType != conf.SURVEY_CLASS_NAME:  httpServer.outputJsonError( 'linkKey destinationType=' + str(linkKeyRecord.destinationType), responseData, self.response );  return;
        surveyId = linkKeyRecord.destinationId
        loginRequired = linkKeyRecord.loginRequired

        # User id from cookie, crumb...
        responseData = { 'success':False, 'requestLogId':requestLogId }
        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=loginRequired, loginCrumb=loginCrumb )
        if userId is None: return

        # Check survey length
        if not httpServer.isLengthOk( introduction, '', conf.minLengthSurveyIntro ):
            httpServer.outputJsonError( conf.TOO_SHORT, responseData, self.response )
            return

        # Retrieve survey record.
        surveyRec = survey.Survey.get_by_id( int(surveyId) )
        logging.debug( 'SubmitEditSurvey.post() surveyRec=' + str(surveyRec) )

        if surveyRec is None:  httpServer.outputJsonError( 'survey not found', responseData, self.response );  return;

        # Verify that survey is editable
        if userId != surveyRec.creator:  httpServer.outputJsonError( conf.NOT_OWNER, responseData, self.response );  return;
        if not surveyRec.allowEdit:  httpServer.outputJsonError( conf.HAS_RESPONSES, responseData, self.response );  return;

        # Update survey record.
        surveyRec.introduction = introduction
        surveyRec.put()
        
        # Display updated survey.
        surveyDisplay = httpServerAutocomplete.surveyToDisplay( surveyRec, userId )
        responseData.update(  { 'success':True, 'survey':surveyDisplay }  )
        self.response.out.write( json.dumps( responseData ) )



class ReorderSurveyQuestions( webapp2.RequestHandler ):

    def post(self):
        logging.debug( 'ReorderSurveyQuestions.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        inputData = json.loads( self.request.body )
        logging.debug( 'ReorderSurveyQuestions.post() inputData=' + str(inputData) )

        questionIds = inputData['questionIds']
        linkKeyString = inputData['linkKey']
        browserCrumb = inputData.get( 'crumb', '' )
        loginCrumb = inputData.get( 'crumbForLogin', '' )
        logging.debug( 'ReorderSurveyQuestions.post() questionIds=' + str(questionIds) + ' browserCrumb=' + str(browserCrumb) 
            + ' loginCrumb=' + str(loginCrumb) 
            + ' linkKeyString=' + str(linkKeyString) )



# Retrieve link-key record
        if linkKeyString is None:  httpServer.outputJsonError( 'linkKeyString is null', responseData, self.response );  return;
        linkKeyRecord = linkKey.LinkKey.get_by_id( linkKeyString )
        logging.debug( 'ReorderSurveyQuestions.post() linkKeyRecord=' + str(linkKeyRecord) )

        if linkKeyRecord is None:  httpServer.outputJsonError( 'linkKey not found', responseData, self.response );  return;
        if linkKeyRecord.destinationType != conf.SURVEY_CLASS_NAME:  httpServer.outputJsonError( 'linkKey destinationType=' + str(linkKeyRecord.destinationType), responseData, self.response );  return;
        surveyId = linkKeyRecord.destinationId
        loginRequired = linkKeyRecord.loginRequired

        # User id from cookie, crumb...
        responseData = { 'success':False, 'requestLogId':requestLogId }
        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=loginRequired, loginCrumb=loginCrumb )
        if userId is None: return

        # Retrieve survey record.
        surveyRec = survey.Survey.get_by_id( int(surveyId) )
        logging.debug( 'ReorderSurveyQuestions.post() surveyRec=' + str(surveyRec) )

        if surveyRec is None:  httpServer.outputJsonError( 'survey not found', responseData, self.response );  return;
        if surveyId != linkKeyRecord.destinationId:  httpServer.outputJsonError( 'surveyId != linkKeyRecord.destinationId', responseData, self.response );  return;

        # Verify that survey is editable
        if userId != surveyRec.creator:  httpServer.outputJsonError( conf.NOT_OWNER, responseData, self.response );  return;
        if not surveyRec.allowEdit:  httpServer.outputJsonError( conf.HAS_RESPONSES, responseData, self.response );  return;

        # If questionId is missing from survey record... disallow/remove it.
        questionIdsFromSurveySet = set( surveyRec.questionIds )
        logging.debug( 'ReorderSurveyQuestions.post() questionIdsFromSurveySet=' + str(questionIdsFromSurveySet) )

        questionIdsFromInputFiltered = [ q for q in questionIds  if q in questionIdsFromSurveySet ]
        logging.debug( 'ReorderSurveyQuestions.post() questionIdsFromInputFiltered=' + str(questionIdsFromInputFiltered) )

        # If questionId is missing from input questionIds order... move it to end.
        questionIdSetFromInputSet = set( questionIdsFromInputFiltered )
        logging.debug( 'ReorderSurveyQuestions.post() questionIdSetFromInputSet=' + str(questionIdSetFromInputSet) )

        questionIdsFromSurveyReordered = questionIdsFromInputFiltered + [q for q in surveyRec.questionIds  if q not in questionIdSetFromInputSet]
        logging.debug( 'ReorderSurveyQuestions.post() questionIdsFromSurveyReordered=' + str(questionIdsFromSurveyReordered) )

        # Update survey record.
        surveyRec.questionIds = questionIdsFromSurveyReordered
        surveyRec.put()
        
        # Display updated survey.
        surveyDisplay = httpServerAutocomplete.surveyToDisplay( surveyRec, userId )
        surveyDisplay['questionIds'] = surveyRec.questionIds
        responseData.update(  { 'success':True, 'survey':surveyDisplay }  )
        self.response.out.write( json.dumps( responseData ) )



# Route HTTP request
app = webapp2.WSGIApplication([
    ('/autocomplete/newSurvey', SubmitNewSurvey) ,
    ('/autocomplete/editSurvey', SubmitEditSurvey) ,
    ('/autocomplete/reorderSurveyQuestions', ReorderSurveyQuestions)
])


