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
import reasonVote
import requestForProposals
import user
import text



class SubmitVote(webapp2.RequestHandler):

    @ndb.toplevel   # Ensure that proposal.incrementAsync() completes before finishing execution, but after http response is sent.
    def post(self):

        logging.debug( 'SubmitVote.post() request.body=' + self.request.body )

        # Collect inputs
        requestLogId = os.environ.get( conf.REQUEST_LOG_ID )
        inputData = json.loads( self.request.body )
        logging.debug( 'SubmitVote.post() inputData=' + str(inputData) )

        linkKeyStr = inputData['linkKey']
        reasonId = str( int( inputData['reasonId'] ) )
        voteUp = inputData['vote']
        browserCrumb = inputData['crumb']
        loginCrumb = inputData.get( 'crumbForLogin', '' )
        logging.debug( 'SubmitVote.post() linkKeyStr=' + str(linkKeyStr) + ' reasonId=' + str(reasonId) + ' voteUp=' + str(voteUp) + ' browserCrumb=' + str(browserCrumb) + ' loginCrumb=' + str(loginCrumb) )

        # User id from cookie, crumb...
        responseData = { 'success':False, 'requestLogId':requestLogId }

        # Verify that linkKey matches request/proposal.
        linkKeyRec = linkKey.LinkKey.get_by_id( linkKeyStr )
        if linkKeyRec is None:  httpServer.outputJsonError( 'linkKey not found', responseData, self.response );  return;
        if linkKeyRec.destinationId is None:  httpServer.outputJsonError( 'linkKey.destinationId=null', responseData, self.response );  return;
        logging.debug( 'SubmitVote.post() linkKeyRec=' + str(linkKeyRec) )

        userId = httpServer.getAndCheckUserId( self.request, browserCrumb, responseData, self.response, loginRequired=linkKeyRec.loginRequired, loginCrumb=loginCrumb )
        if not userId:  return

        reasonRecord = reason.Reason.get_by_id( int(reasonId) )
        if reasonRecord is None:  httpServer.outputJsonError( 'reasonId not found', responseData, self.response );  return;
        logging.debug( 'reasonRecord=' + str(reasonRecord) )

        isRequestForProposals = False
        if linkKeyRec.destinationType == conf.PROPOSAL_CLASS_NAME:
            # Verify that reason belongs to linkKey's proposal.
            if reasonRecord.proposalId != linkKeyRec.destinationId:  httpServer.outputJsonError( 'reasonRecord.proposalId != linkKeyRec.destinationId', responseData, self.response );  return;

        elif linkKeyRec.destinationType == conf.REQUEST_CLASS_NAME:
            # Verify that reason belongs to linkKey's request.
            if reasonRecord.requestId != linkKeyRec.destinationId:  httpServer.outputJsonError( 'reasonRecord.requestId != linkKeyRec.destinationId', responseData, self.response );  return;
            isRequestForProposals = True
        else:
            httpServer.outputJsonError( 'linkKey destinationType=' + linkKeyRec.destinationType, responseData, self.response );  return;

        # Set vote, update vote count -- using transactions and retry.
        success, reasonRecordUpdated, voteRecord = reason.vote( 
            reasonRecord.requestId, reasonRecord.proposalId, reasonId, userId, voteUp, isRequestForProposals=isRequestForProposals )
        logging.debug( 'success=' + str(success) + ' reasonRecordUpdated=' + str(reasonRecordUpdated) + ' voteRecord=' + str(voteRecord) )
        if not success:  httpServer.outputJsonError( 'reason.vote() success=false', responseData, self.response );  return;
        if reasonRecordUpdated is not None:  reasonRecord = reasonRecordUpdated
        
        # Display reason and votes.
        reasonDisplay = httpServer.reasonToDisplay( reasonRecord, userId )
        reasonDisplay['myVote'] =  voteRecord.voteUp and ( str(voteRecord.reasonId) == str(reasonRecord.key.id()) )
        responseData.update(  { 'success':success, 'reason':reasonDisplay }  )
        logging.debug( 'responseData=' + str(responseData) )
        
        self.response.out.write( json.dumps( responseData ) )
        logging.debug( 'SubmitVote.post() done' )

        # Mark reason as not editable.
        if reasonRecord.allowEdit:
            reason.setEditable( reasonId, False )


# Route HTTP request
app = webapp2.WSGIApplication([
    ('/submitVote', SubmitVote)
])


