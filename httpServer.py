# Shared functions for all http request service classes.


# Import external modules.
import json
import logging
# Import app modules.
from configuration import const as conf
import linkKey
import user


########################################################################

def isLengthOk( title, detail, lengthMin ):
    totalLength = 0
    totalLength += len(title) if title  else 0
    totalLength += len(detail) if detail  else 0;
    logging.debug( 'isLengthOk() totalLength={} lengthMin={}'.format( totalLength, lengthMin ) )
    return ( totalLength >= lengthMin )


# Returns userId, or returns None and modifies responseData and httpResponse to report error.
def getAndCheckUserId( httpRequest, inputCrumb, responseData, httpResponse, loginRequired=False, loginCrumb=None ):

    userId = user.getCookieId( httpRequest, loginRequired=loginRequired )   # User id cookie created by main page only
    logging.debug( 'httpServer.getAndCheckUserId() userId=' + str(userId) )

    if userId is None:
        errorMessage = conf.NO_LOGIN if loginRequired  else conf.NO_COOKIE
        outputJsonError( errorMessage, responseData, httpResponse )
        return None
    if not user.checkCrumb( userId, inputCrumb, loginRequired=loginRequired, loginCrumb=loginCrumb ):
        outputJsonError( conf.BAD_CRUMB, responseData, httpResponse )
        return None
    return userId


# Modifies responseData and httpResponse.
def outputJsonError( message, responseData, httpResponse ):
    responseData['success'] = False
    responseData['message'] = message
    logging.debug( 'httpServer.outputJsonError() message=' + message )
    httpResponse.out.write( json.dumps( responseData ) )


# Creates link-key, stores link-key in persistent record, and adds link-key to recent links in cookie.
def createAndStoreLinkKey( destClassName, destinationId, loginRequired, httpRequest, httpResponse ):
    linkKeyString = linkKey.createLinkKey()
    logging.debug( 'linkKeyString={}'.format(linkKeyString) )

    linkKeyRecord = linkKey.LinkKey(
        id = linkKeyString,
        destinationType = destClassName,
        destinationId = destinationId,
        loginRequired = loginRequired
    )
    linkKeyRecordKey = linkKeyRecord.put()
    user.storeRecentLinkKey( linkKeyString, httpRequest, httpResponse )
    return linkKeyRecord



########################################################################
# Filtering / transforming persistent record fields for display

def linkKeyToDisplay( linkKeyRecord ):
    return {
        'loginRequired': (linkKeyRecord.loginRequired == True) ,
        'id': linkKeyRecord.key.id()
    }

def requestToDisplay( requestRecord, userId ):
    return {
        'id': str(requestRecord.key.id()),
        'title': requestRecord.title,
        'detail': requestRecord.detail,
        'mine': (requestRecord.creator == userId),
        'allowEdit': (userId == requestRecord.creator) and requestRecord.allowEdit
    }

def proposalToDisplay( proposalRecord, userId ):
    return {
        'id': str(proposalRecord.key.id()),
        'title': proposalRecord.title,
        'detail': proposalRecord.detail,
        'mine': (proposalRecord.creator == userId),
        'allowEdit': (userId == proposalRecord.creator) and proposalRecord.allowEdit
    }

def reasonToDisplay( reasonRecord, userId ):
    return {
        'proposalId': reasonRecord.proposalId,
        'id': str(reasonRecord.key.id()),
        'content': reasonRecord.content,
        'proOrCon': reasonRecord.proOrCon,
        'mine': (reasonRecord.creator == userId),
        'allowEdit': (userId == reasonRecord.creator) and reasonRecord.allowEdit,
        'voteCount': reasonRecord.voteCount,
        'score': reasonRecord.score
    }

