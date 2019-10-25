# Import external modules
from google.appengine.ext import ndb
import json
import logging
import os
import webapp2
# Import app modules
from configuration import const as conf
import httpServer
import linkKey
import requestForProposals
import text
import user




class SubmitNewRequest(webapp2.RequestHandler):

    def post(self):  # Not a transaction, because it is ok to fail link creation, and orphan the request.

        logging.debug( 'SubmitNewRequest.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        inputData = json.loads( self.request.body )
        logging.debug( 'SubmitNewRequest.post() inputData=' + str(inputData) )

        title = text.formTextToStored( inputData.get('title', '') )
        detail = text.formTextToStored( inputData.get('detail', '') )
        loginRequired = inputData.get( 'loginRequired', False )
        browserCrumb = inputData.get( 'crumb', '' )
        loginCrumb = inputData.get( 'crumbForLogin', '' )
        logging.debug( 'SubmitNewRequest.post() title=' + str(title) + ' detail=' + str(detail) + ' browserCrumb=' + str(browserCrumb) + ' loginCrumb=' + str(loginCrumb) + ' loginRequired=' + str(loginRequired) )

        # User id from cookie, crumb...
        responseData = { 'success':False, 'requestLogId':requestLogId }
        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=loginRequired, loginCrumb=loginCrumb )
        if userId is None: return

        # Check request length
        if not httpServer.isLengthOk( title, detail, conf.minLengthRequest ):
            httpServer.outputJsonError( conf.TOO_SHORT, responseData, self.response )
            return
        
        # Construct new request record
        requestRecord = requestForProposals.RequestForProposals(
            creator=userId,
            title=title,
            detail=detail,
            allowEdit=True,
        )
        # Store request record
        requestRecordKey = requestRecord.put()
        logging.debug( 'requestRecordKey.id={}'.format(requestRecordKey.id()) )
        
        # Construct and store link key.
        requestId = str( requestRecordKey.id() )
        linkKeyRecord = httpServer.createAndStoreLinkKey( conf.REQUEST_CLASS_NAME, requestId, loginRequired, self.request, self.response )
        
        # Send response data.
        linkKeyDisplay = httpServer.linkKeyToDisplay( linkKeyRecord )
        requestDisplay = httpServer.requestToDisplay( requestRecord, userId )
        responseData.update(  { 'success':True, 'linkKey':linkKeyDisplay, 'request':requestDisplay }  )
        self.response.out.write( json.dumps( responseData ) )



class SubmitEditRequest(webapp2.RequestHandler):

    def post(self):
        logging.debug( 'SubmitEditRequest.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        inputData = json.loads( self.request.body )
        logging.debug( 'SubmitEditRequest.post() inputData=' + str(inputData) )

        title = text.formTextToStored( inputData.get('inputTitle', '') )
        detail = text.formTextToStored( inputData.get('inputDetail', '') )
        linkKeyString = inputData.get( 'linkKey', None )
        browserCrumb = inputData.get( 'crumb', '' )
        loginCrumb = inputData.get( 'crumbForLogin', '' )
        logging.debug( 'SubmitEditRequest.post() title=' + str(title) + ' detail=' + str(detail) + ' browserCrumb=' + str(browserCrumb) + ' loginCrumb=' + str(loginCrumb) + ' linkKeyString=' + str(linkKeyString) )

        # User id from cookie, crumb...
        responseData = { 'success':False, 'requestLogId':requestLogId }

        # Require link-key, and convert it to requestId.
        linkKeyRec = linkKey.LinkKey.get_by_id( linkKeyString )
        logging.debug( 'SubmitEditRequest.post() linkKeyRec=' + str(linkKeyRec) )

        if linkKeyRec is None:  httpServer.outputJsonError( 'linkKey not found', responseData, self.response );  return;
        if linkKeyRec.destinationType != conf.REQUEST_CLASS_NAME:  httpServer.outputJsonError( 'linkKey not a request', responseData, self.response );  return;
        requestId = int(linkKeyRec.destinationId)
        logging.debug( 'SubmitEditRequest.post() requestId=' + str(requestId) )

        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=linkKeyRec.loginRequired, loginCrumb=loginCrumb )
        if not userId:  return

        # Check request length.
        if not httpServer.isLengthOk( title, detail, conf.minLengthRequest ):
            httpServer.outputJsonError( conf.TOO_SHORT, responseData, self.response )
            return
        
        # Retrieve request record.
        requestForProposalsRec = requestForProposals.RequestForProposals.get_by_id( requestId )
        logging.debug( 'SubmitEditRequest.post() requestForProposalsRec=' + str(requestForProposalsRec) )
        if requestForProposalsRec is None:  httpServer.outputJsonError( 'requestForProposalsRec not found', responseData, self.response );  return;

        # Verify that request is editable.
        if userId != requestForProposalsRec.creator:
            httpServer.outputJsonError( conf.NOT_OWNER, responseData, self.response )
            return
        if not requestForProposalsRec.allowEdit:
            httpServer.outputJsonError( conf.HAS_RESPONSES, responseData, self.response )
            return

        # Update request record.
        requestForProposalsRec.title = title
        requestForProposalsRec.detail = detail
        requestForProposalsRec.put()
        
        linkKeyDisplay = httpServer.linkKeyToDisplay( linkKeyRec )
        requestDisplay = httpServer.requestToDisplay( requestForProposalsRec, userId )
        responseData.update(  { 'success':True, 'linkKey':linkKeyDisplay, 'request':requestDisplay }  )
        self.response.out.write( json.dumps( responseData ) )



# Route HTTP request
app = webapp2.WSGIApplication([
    ('/newRequest', SubmitNewRequest),
    ('/editRequest', SubmitEditRequest)
])


