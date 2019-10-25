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



class SubmitNewProposal(webapp2.RequestHandler):

    def post(self):

        logging.debug( 'SubmitNewProposal.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        responseData = { 'success':False, 'requestLogId':requestLogId }
        inputData = json.loads( self.request.body )
        logging.debug( 'SubmitNewProposal.post() inputData=' + str(inputData) )

        title = text.formTextToStored( inputData.get('title', '') )
        detail = text.formTextToStored( inputData.get('detail', '') )
        loginRequired = inputData.get( 'loginRequired', False )
        browserCrumb = inputData.get( 'crumb', '' )
        loginCrumb = inputData.get( 'crumbForLogin', '' )
        logging.debug( 'SubmitNewProposal.post() title=' + str(title) + ' detail=' + str(detail) + ' browserCrumb=' + str(browserCrumb) + ' loginCrumb=' + str(loginCrumb) + ' loginRequired=' + str(loginRequired) )

        # Voter login not required to create initial proposal, though login may be required to use proposal
        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=loginRequired, loginCrumb=loginCrumb )
        if userId is None: return

        # Check proposal length.
        if not httpServer.isLengthOk( title, detail, conf.minLengthProposal ):  httpServer.outputJsonError( conf.TOO_SHORT, responseData, self.response );  return;
        
        # Construct new proposal record.
        proposalRecord = proposal.Proposal(
            creator=userId,
            title=title,
            detail=detail,
            allowEdit=True,
        )
        # Store proposal record.
        proposalRecordKey = proposalRecord.put()
        logging.debug( 'proposalRecordKey.id={}'.format(proposalRecordKey.id()) )

        # Construct and store link key.
        proposalId = str( proposalRecordKey.id() )
        proposalLinkKeyRecord = httpServer.createAndStoreLinkKey( conf.PROPOSAL_CLASS_NAME, proposalId, loginRequired, self.request, self.response )

        # Display proposal
        linkKeyDisplay = httpServer.linkKeyToDisplay( proposalLinkKeyRecord )
        proposalDisplay = httpServer.proposalToDisplay( proposalRecord, userId )
        responseData.update(  { 'success':True, 'linkKey':linkKeyDisplay, 'proposal':proposalDisplay }  )
        self.response.out.write( json.dumps( responseData ) )



class SubmitNewProposalForRequest(webapp2.RequestHandler):

    def post(self):

        logging.debug( 'SubmitNewProposalForRequest.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        responseData = { 'success':False, 'requestLogId':requestLogId }
        inputData = json.loads( self.request.body )
        logging.debug( 'SubmitNewProposalForRequest.post() inputData=' + str(inputData) )

        requestLinkKeyStr = inputData['requestId']
        title = text.formTextToStored( inputData['title'] )
        detail = text.formTextToStored( inputData['detail'] )
        initialReason1 = text.formTextToStored( inputData.get( 'initialReason1', None ) )
        initialReason2 = text.formTextToStored( inputData.get( 'initialReason2', None ) )
        initialReason3 = text.formTextToStored( inputData.get( 'initialReason3', None ) )
        browserCrumb = inputData['crumb']
        loginCrumb = inputData.get( 'crumbForLogin', '' )
        logging.debug( 'SubmitNewProposalForRequest.post() requestLinkKeyStr=' + str(requestLinkKeyStr) + ' title=' + str(title) + ' detail=' + str(detail) + ' browserCrumb=' + str(browserCrumb) + ' loginCrumb=' + str(loginCrumb) )

        # Check proposal length
        if not httpServer.isLengthOk( title, detail, conf.minLengthProposal ):  httpServer.outputJsonError( conf.TOO_SHORT, responseData, self.response );  return;
        initialReasons = [ r for r in [ initialReason1, initialReason2, initialReason3 ] if r is not None ]
        for initialReason in initialReasons:
            if initialReason is not None and not httpServer.isLengthOk( initialReason, None, conf.minLengthReason ):  httpServer.outputJsonError( conf.REASON_TOO_SHORT, responseData, self.response );  return;

        # Require link-key, and convert it to requestId.
        if requestLinkKeyStr is None:  httpServer.outputJsonError( 'requestLinkKeyStr is null', responseData, self.response );  return;
        requestLinkKeyRec = linkKey.LinkKey.get_by_id( requestLinkKeyStr )
        logging.debug( 'SubmitNewProposalForRequest.post() requestLinkKeyRec=' + str(requestLinkKeyRec) )

        if requestLinkKeyRec is None:  httpServer.outputJsonError( 'requestLinkKey not found', responseData, self.response );  return;
        if requestLinkKeyRec.destinationType != conf.REQUEST_CLASS_NAME:  httpServer.outputJsonError( 'requestLinkKey not a request', responseData, self.response );  return;
        requestId = requestLinkKeyRec.destinationId

        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=requestLinkKeyRec.loginRequired, loginCrumb=loginCrumb )
        if not userId:  return

        # Get user id from cookie
        requestRec = requestForProposals.RequestForProposals.get_by_id( int(requestId) )
        if not requestRec:  return
        
        # Construct new proposal record
        proposalRecord = proposal.Proposal(
            requestId=requestId,
            creator=userId,
            title=title,
            detail=detail,
            allowEdit = ( len(initialReasons) == 0 )
        )
        # Store proposal record
        proposalRecordKey = proposalRecord.put()
        proposalId = str( proposalRecordKey.id() )
        logging.debug( 'proposalRecordKey.id={}'.format(proposalRecordKey.id()) )

        # For each initial reason...
        reasonDisplays = []
        for initialReason in initialReasons:
            # Construct new reason record.
            reasonRecord = reason.Reason(
                requestId=requestId,
                proposalId=proposalId,
                creator=userId,
                proOrCon= conf.PRO,
                content= initialReason,
                allowEdit=True
            )
            # Store reason record.
            reasonRecordKey = reasonRecord.put()
            logging.debug( 'reasonRecordKey={}'.format(reasonRecordKey) )

            # Convert reason for display.
            reasonDisplays.append(  httpServer.reasonToDisplay( reasonRecord, userId )  )

        # Display proposal.
        proposalDisplay = httpServer.proposalToDisplay( proposalRecord, userId )
        responseData.update(  { 'success':True, 'proposal':proposalDisplay, 'reasons':reasonDisplays }  )
        self.response.out.write( json.dumps( responseData ) )

        # Mark request-for-proposals as not editable.
        if ( requestRec.allowEdit ):
            requestForProposals.setEditable( requestId, False )


class SubmitEditProposal(webapp2.RequestHandler):

    def post(self):
        logging.debug( 'SubmitEditProposal.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        inputData = json.loads( self.request.body )
        logging.debug( 'SubmitEditProposal.post() inputData=' + str(inputData) )

        title = text.formTextToStored( inputData['title'] )
        detail = text.formTextToStored( inputData['detail'] )
        linkKeyString = inputData['linkKey']
        proposalId = str( int( inputData['proposalId'] ) )
        browserCrumb = inputData['crumb']
        loginCrumb = inputData.get( 'crumbForLogin', '' )
        logging.debug( 'SubmitEditProposal.post() title=' + str(title) + ' detail=' + str(detail) + ' browserCrumb=' + str(browserCrumb) + ' loginCrumb=' + str(loginCrumb) + ' linkKeyString=' + str(linkKeyString) + ' proposalId=' + str(proposalId) )

        # User id from cookie, crumb...
        responseData = { 'success':False, 'requestLogId':requestLogId }

        # Check proposal length
        if not httpServer.isLengthOk( title, detail, conf.minLengthProposal ):
            httpServer.outputJsonError( conf.TOO_SHORT, responseData, self.response )
            return

        # Require link-key.
        linkKeyRec = linkKey.LinkKey.get_by_id( linkKeyString )
        logging.debug( 'SubmitEditProposal.post() linkKeyRec=' + str(linkKeyRec) )

        if linkKeyRec is None:  httpServer.outputJsonError( 'linkKey not found', responseData, self.response );  return;

        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=linkKeyRec.loginRequired, loginCrumb=loginCrumb )
        if not userId:  return

        # Retrieve proposal record.
        proposalRec = proposal.Proposal.get_by_id( int(proposalId) )
        logging.debug( 'SubmitEditProposal.post() proposalRec=' + str(proposalRec) )

        if proposalRec is None:  httpServer.outputJsonError( 'proposal not found', responseData, self.response );  return;

        # Verify that proposal matches link-key.
        if linkKeyRec.destinationType == conf.REQUEST_CLASS_NAME:
            if proposalRec.requestId != linkKeyRec.destinationId:  httpServer.outputJsonError( 'proposalRec.requestId != linkKeyRec.destinationId', responseData, self.response );  return;

        elif linkKeyRec.destinationType == conf.PROPOSAL_CLASS_NAME:
            if proposalId != linkKeyRec.destinationId:  httpServer.outputJsonError( 'proposalId != linkKeyRec.destinationId', responseData, self.response );  return;

        else: httpServer.outputJsonError( 'linkKey destinationType=' + str(linkKeyRec.destinationType), responseData, self.response );  return;

        # Verify that proposal is editable
        if userId != proposalRec.creator:
            httpServer.outputJsonError( conf.NOT_OWNER, responseData, self.response )
            return
        if not proposalRec.allowEdit:
            httpServer.outputJsonError( conf.HAS_RESPONSES, responseData, self.response )
            return

        # Update proposal record.
        proposalRec.title = title
        proposalRec.detail = detail
        proposalRec.put()
        
        # Display updated proposal.
        proposalDisplay = httpServer.proposalToDisplay( proposalRec, userId )
        responseData.update(  { 'success':True, 'proposal':proposalDisplay }  )
        self.response.out.write( json.dumps( responseData ) )



# Route HTTP request
app = webapp2.WSGIApplication([
    ('/newProposal', SubmitNewProposal),
    ('/newProposalForRequest', SubmitNewProposalForRequest),
    ('/editProposal', SubmitEditProposal)
])


