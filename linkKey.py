# External imports
from google.appengine.ext import ndb
# Local imports
from constants import Constants
from user import randomStringWithLength


# Constants
const = Constants()
const.LINK_KEY_LENGTH = 50


# Parent key: none
# Key: long random alpha-numeric string
class LinkKey(ndb.Model):
    destinationType = ndb.StringProperty()  # { REQUEST_CLASS_NAME, PROPOSAL_CLASS_NAME }
    destinationId = ndb.StringProperty()
    loginRequired = ndb.BooleanProperty()



def createLinkKey():
    return randomStringWithLength( const.LINK_KEY_LENGTH )


