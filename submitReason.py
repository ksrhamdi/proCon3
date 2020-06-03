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
        cookieData = httpServer.validate( self.request, inputData, responseData, self.response )
        if not cookieData.valid():  return
        userId = cookieData.id()

        # Check reason length.
        if not httpServer.isLengthOk( reasonContent, '', conf.minLengthReason ):  return httpServer.outputJson( cookieData, responseData, self.response, errorMessage=conf.TOO_SHORT )

        # Retrieve link-key record
        linkKeyRec = linkKey.LinkKey.get_by_id( linkKeyStr )
        if linkKeyRec is None:  return httpServer.outputJson( cookieData, responseData, self.response, errorMessage='linkKey not found' )
        logging.debug( 'SubmitNewReason.post() linkKeyRec=' + str(linkKeyRec) )

        if linkKeyRec.loginRequired  and  not cookieData.loginId:  return httpServer.outputJson( cookieData, responseData, self.response, errorMessage=conf.NO_LOGIN )

        # Retrieve proposal record
        proposalRec = proposal.Proposal.get_by_id( int(proposalId) )
        if proposalRec is None:  return httpServer.outputJson( cookieDataresponseData, self.response, errorMessage='proposal not found' )
        logging.debug( 'SubmitNewReason.post() proposalRec=' + str(proposalRec) )

        # Check link key
        requestId = None
        if linkKeyRec.destinationType == conf.PROPOSAL_CLASS_NAME:
            # Verify that reason belongs to linkKey's proposal.
            if proposalId != linkKeyRec.destinationId:  return httpServer.outputJson( cookieData, responseData, self.response, errorMessage='proposalId != linkKeyRec.destinationId' )

        elif linkKeyRec.destinationType == conf.REQUEST_CLASS_NAME:
            # Verify that reason belongs to linkKey's request, via proposal record.
            requestId = proposalRec.requestId
            if requestId != linkKeyRec.destinationId:  return httpServer.outputJson( cookieData, responseData, self.response, errorMessage='requestId != linkKeyRec.destinationId' )
        else:
            return httpServer.outputJson( cookieData, responseData, self.response, errorMessage='linkKey destinationType=' + linkKeyRec.destinationType )
        
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
        httpServer.outputJson( cookieData, responseData, self.response )

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
        cookieData = httpServer.validate( self.request, inputData, responseData, self.response )
        if not cookieData.valid():  return
        userId = cookieData.id()

        # Check reason length.
        if not httpServer.isLengthOk( reasonContent, '', conf.minLengthReason ):  return httpServer.outputJson( cookieData, responseData, self.response, errorMessage=conf.TOO_SHORT )

        # Retrieve link-key record
        linkKeyRec = linkKey.LinkKey.get_by_id( linkKeyStr )
        if linkKeyRec is None:  return httpServer.outputJson( cookieData, responseData, self.response, errorMessage='linkKey not found' )
        logging.debug( 'SubmitEditReason.post() linkKeyRec=' + str(linkKeyRec) )

        if linkKeyRec.loginRequired  and  not cookieData.loginId:  return httpServer.outputJson( cookieData, responseData, self.response, errorMessage=conf.NO_LOGIN )

        # Verify that reason belongs to request.
        reasonRec = reason.Reason.get_by_id( int(reasonId) )
        if reasonRec is None:  return httpServer.outputJson( cookieData, responseData, self.response, errorMessage='reason not found' )
        logging.debug( 'SubmitEditReason.post() reasonRec=' + str(reasonRec) )

        # Check link key
        if linkKeyRec.destinationType == conf.PROPOSAL_CLASS_NAME:
            # Verify that reason belongs to linkKey's proposal.
            if reasonRec.proposalId != linkKeyRec.destinationId:  return httpServer.outputJson( cookieData, responseData, self.response, errorMessage='reasonRec.proposalId != linkKeyRec.destinationId' )

        elif linkKeyRec.destinationType == conf.REQUEST_CLASS_NAME:
            # Verify that reason belongs to linkKey's request.
            if reasonRec.requestId != linkKeyRec.destinationId:  return httpServer.outputJson( cookieData, responseData, self.response, errorMessage='reasonRec.requestId != linkKeyRec.destinationId' )

        else:
            httpServer.outputJson( cookieData, responseData, self.response, errorMessage='linkKey destinationType=' + linkKeyRec.destinationType )

        # Verify that proposal is editable
        if userId != reasonRec.creator:  return httpServer.outputJson( cookieData, responseData, self.response, errorMessage=conf.NOT_OWNER )
        if not reasonRec.allowEdit:  httpServer.outputJson( cookieData, responseData, self.response, errorMessage=conf.HAS_RESPONSES )

        # Update reason record.
        reasonRec.content = reasonContent
        reasonRec.put()
        
        # Display reason.
        reasonDisplay = httpServer.reasonToDisplay( reasonRec, userId )
        responseData.update(  { 'success':True, 'reason':reasonDisplay }  )
        httpServer.outputJson( cookieData, responseData, self.response )


# Route HTTP request
app = webapp2.WSGIApplication([
    ('/newReason', SubmitNewReason) ,
    ('/editReason', SubmitEditReason)
])


