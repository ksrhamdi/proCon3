# Simple list of site URLs


# Import external modules
import jinja2
import logging
import os
import webapp2
# Import local modules
import configuration
import user


# Parameters
JINJA_ENVIRONMENT = jinja2.Environment(
    loader = jinja2.FileSystemLoader( os.path.dirname(__file__) ),
    extensions = ['jinja2.ext.autoescape'],
    autoescape = True
)


# Main page generator
class SiteList( webapp2.RequestHandler ):

    def get(self):
        # set cookie
        userId = user.getAndCreateBrowserIdCookie( self.request, self.response )

        templateValues = { }
        template = JINJA_ENVIRONMENT.get_template('siteList.html')
        self.response.write( template.render(templateValues) )


# Route URLs to page generators
app = webapp2.WSGIApplication([
    ('/', SiteList),
])

