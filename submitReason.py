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
import proposal
import reason
import requestForProposals
import user
import text



class SubmitNewReason(webapp2.RequestHandler):

    def post(self):

        logging.debug( 'SubmitNewReason.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        inputData = json.loads( self.request.body )
        logging.debug( 'SubmitNewReason.post() inputData=' + str(inputData) )

        linkKeyStr = inputData.get( 'linkKey', None )
        proposalId = str( int( inputData.get( 'proposalId', None ) ) )
        proOrCon = inputData.get( 'proOrCon', None )
        reasonContent = text.formTextToStored( inputData.get('reasonContent', '') )
        browserCrumb = inputData.get( 'crumb', '' )
        loginCrumb = inputData.get( 'crumbForLogin', '' )
        logging.debug( 'SubmitNewReason.post() linkKeyStr=' + str(linkKeyStr) + ' proposalId=' + str(proposalId) 
            + ' proOrCon=' + str(proOrCon) + ' reasonContent=' + str(reasonContent) 
            + ' browserCrumb=' + str(browserCrumb) + loginCrumb + str(loginCrumb) )

        # User id from cookie, crumb...
        responseData = { 'success':False, 'requestLogId':requestLogId }

        # Check reason length.
        if not httpServer.isLengthOk( reasonContent, '', conf.minLengthReason ):  httpServer.outputJsonError( conf.TOO_SHORT, responseData, self.response );  return;

        # Retrieve link-key record
        linkKeyRec = linkKey.LinkKey.get_by_id( linkKeyStr )
        if linkKeyRec is None:  httpServer.outputJsonError( 'linkKey not found', responseData, self.response );  return;
        logging.debug( 'SubmitNewReason.post() linkKeyRec=' + str(linkKeyRec) )

        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=linkKeyRec.loginRequired, loginCrumb=loginCrumb )
        if not userId:  return

        # Retrieve proposal record
        proposalRec = proposal.Proposal.get_by_id( int(proposalId) )
        if proposalRec is None:  httpServer.outputJsonError( 'proposal not found', responseData, self.response );  return;
        logging.debug( 'SubmitNewReason.post() proposalRec=' + str(proposalRec) )

        # Check link key
        requestId = None
        if linkKeyRec.destinationType == conf.PROPOSAL_CLASS_NAME:
            # Verify that reason belongs to linkKey's proposal.
            if proposalId != linkKeyRec.destinationId:  httpServer.outputJsonError( 'proposalId != linkKeyRec.destinationId', responseData, self.response );  return;

        elif linkKeyRec.destinationType == conf.REQUEST_CLASS_NAME:
            # Verify that reason belongs to linkKey's request, via proposal record.
            requestId = proposalRec.requestId
            if requestId != linkKeyRec.destinationId:  httpServer.outputJsonError( 'requestId != linkKeyRec.destinationId', responseData, self.response );  return;
        else:
            httpServer.outputJsonError( 'linkKey destinationType=' + linkKeyRec.destinationType, responseData, self.response );  return;
        
        # Construct new reason record
        reasonRecord = reason.Reason(
            requestId=requestId,
            proposalId=proposalId,
            creator=userId,
            proOrCon=proOrCon,
            content=reasonContent,
            allowEdit=True
        )
        # Store reason record
        reasonRecordKey = reasonRecord.put()
        logging.debug( 'reasonRecordKey={}'.format(reasonRecordKey) )

        # Display reason
        reasonDisplay = httpServer.reasonToDisplay( reasonRecord, userId )
        responseData.update(  { 'success':True, 'reason':reasonDisplay }  )
        self.response.out.write( json.dumps( responseData ) )

        # Mark proposal as not editable.
        if proposalRec.allowEdit:
            proposal.setEditable( proposalId, False )
        


class SubmitEditReason(webapp2.RequestHandler):

    def post(self):
        logging.debug( 'SubmitEditReason.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        inputData = json.loads( self.request.body )
        logging.debug( 'SubmitEditReason.post() inputData=' + str(inputData) )

        linkKeyStr = inputData.get( 'linkKey', None )
        reasonId = str( int( inputData.get( 'reasonId', None ) ) )
        reasonContent = text.formTextToStored( inputData.get('inputContent', '') )
        browserCrumb = inputData.get( 'crumb', '' )
        loginCrumb = inputData.get( 'crumbForLogin', '' )
        logging.debug( 'SubmitEditReason.post() linkKeyStr=' + str(linkKeyStr) + ' reasonId=' + str(reasonId)
            + ' reasonContent=' + str(reasonContent) + ' browserCrumb=' + str(browserCrumb) + ' loginCrumb=' + str(loginCrumb) )

        # User id from cookie, crumb...
        responseData = { 'success':False, 'requestLogId':requestLogId }

        # Check reason length.
        if not httpServer.isLengthOk( reasonContent, '', conf.minLengthReason ):  httpServer.outputJsonError( conf.TOO_SHORT, responseData, self.response );  return;

        # Retrieve link-key record
        linkKeyRec = linkKey.LinkKey.get_by_id( linkKeyStr )
        if linkKeyRec is None:  httpServer.outputJsonError( 'linkKey not found', responseData, self.response );  return;
        logging.debug( 'SubmitEditReason.post() linkKeyRec=' + str(linkKeyRec) )

        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=linkKeyRec.loginRequired, loginCrumb=loginCrumb )
        if not userId:  return

        # Verify that reason belongs to request.
        reasonRec = reason.Reason.get_by_id( int(reasonId) )
        if reasonRec is None:  httpServer.outputJsonError( 'reason not found', responseData, self.response );  return;
        logging.debug( 'SubmitEditReason.post() reasonRec=' + str(reasonRec) )

        # Check link key
        if linkKeyRec.destinationType == conf.PROPOSAL_CLASS_NAME:
            # Verify that reason belongs to linkKey's proposal.
            if reasonRec.proposalId != linkKeyRec.destinationId:  httpServer.outputJsonError( 'reasonRec.proposalId != linkKeyRec.destinationId', responseData, self.response );  return;

        elif linkKeyRec.destinationType == conf.REQUEST_CLASS_NAME:
            # Verify that reason belongs to linkKey's request.
            if reasonRec.requestId != linkKeyRec.destinationId:  httpServer.outputJsonError( 'reasonRec.requestId != linkKeyRec.destinationId', responseData, self.response );  return;

        else:
            httpServer.outputJsonError( 'linkKey destinationType=' + linkKeyRec.destinationType, responseData, self.response );  return;

        # Verify that proposal is editable
        if userId != reasonRec.creator:  httpServer.outputJsonError( conf.NOT_OWNER, responseData, self.response );  return;
        if not reasonRec.allowEdit:  httpServer.outputJsonError( conf.HAS_RESPONSES, responseData, self.response );  return;

        # Update reason record.
        reasonRec.content = reasonContent
        reasonRec.put()
        
        # Display reason.
        reasonDisplay = httpServer.reasonToDisplay( reasonRec, userId )
        responseData.update(  { 'success':True, 'reason':reasonDisplay }  )
        self.response.out.write( json.dumps( responseData ) )


# Route HTTP request
app = webapp2.WSGIApplication([
    ('/newReason', SubmitNewReason) ,
    ('/editReason', SubmitEditReason)
])


