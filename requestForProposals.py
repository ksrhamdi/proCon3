# Import external modules.
from google.appengine.ext import ndb
import logging
# Import local modules.
from configuration import const as conf
from constants import Constants


const = Constants()
const.MAX_RETRY = 3


# Parent key: none
class RequestForProposals(ndb.Model):
    title = ndb.StringProperty()
    detail = ndb.StringProperty()
    creator = ndb.StringProperty()
    allowEdit = ndb.BooleanProperty()


# @ndb.transactional_async( retries=const.MAX_RETRY )
# @ndb.tasklet
@ndb.transactional( retries=const.MAX_RETRY )
def setEditable( requestId, editable ):
    logging.debug( 'setEditable() editable={}'.format(editable) )
    requestRecord = RequestForProposals.get_by_id( int(requestId) )
    requestRecord.allowEdit = editable
    requestRecord.put()

