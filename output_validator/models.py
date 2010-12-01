import base64
import cPickle
import copy
import datetime
import os
import tempfile

from django.core.handlers.modpython import ModPythonRequest
from django.db import models


class ValidationFailure(models.Model):
    timestamp = models.DateTimeField("Time", default=datetime.datetime.now)
    path = models.TextField("Request path")
    method = models.CharField("HTTP method", max_length=6)
    request = models.TextField("Request object", default='', blank=True)
    response = models.TextField("Response object", default='', blank=True)
    errors = models.TextField("Errors")

    def __repr__(self):
        return self.method + " " + self.path

    def get_request_formatted(self):
        import cPickle
        try:
            return repr(cPickle.loads(base64.decodestring(self.request)))
        except EOFError, UnpicklingError:
            return None

    def get_response(self):
        import cPickle
        try:
            return cPickle.loads(base64.decodestring(self.response))
        except EOFError, UnpicklingError:
            return None

    class Meta:
        ordering = ('-timestamp',)

    class Admin:
        fields =  (
            (None, {'fields': ('timestamp', 'path', 'method', 'errors')}),
        )


    def do_validation(request, response):
        """
        Do validation on response and log if it fails.
        """
        from django.conf import settings
        try:
            OUTPUT_VALIDATOR_IGNORE_PATHS = settings.OUTPUT_VALIDATOR_IGNORE_PATHS
        except AttributeError:
            OUTPUT_VALIDATOR_IGNORE_PATHS = ()


        try:
            content_type = response['Content-Type'].split(';')[0]
            validator = settings.OUTPUT_VALIDATOR_VALIDATORS[content_type]
        except KeyError, IndexError:
            # no content type, or no validator for that content type
            return

        for ignore_path in OUTPUT_VALIDATOR_IGNORE_PATHS:
            if request.path.startswith(ignore_path):
                return

        # first store data in temporary file
        (tmpfilehandle, tmpfilepath) = tempfile.mkstemp()
        os.write(tmpfilehandle, response.content)
        os.close(tmpfilehandle)

        # Now execute validator and get result
        (child_stdin, child_output) = os.popen4(validator + ' ' + tmpfilepath)
        errors = child_output.read()

        # Normalise output so that we can eliminate duplicate errors
        errors = errors.replace(tmpfilepath, '[tmpfilepath]')

        # clean up
        child_stdin.close()
        child_output.close()
        os.unlink(tmpfilepath)

        # Only save if there was an error, and there isn't already
        # a failure saved at the same URL with identical errors.
        # (this isn't perfectly watertight -- you could by chance be
        # generating identical errors with different query strings or
        # POST data, but it's unlikely).

        if len(errors) > 0 and \
               ValidationFailure.objects.filter(errors=errors,
                                                path=request.path).count() == 0:
            failure = ValidationFailure(errors=errors)
            failure.path = request.path
            qs = request.META.get('QUERY_STRING','')
            if qs is not None and len(qs) > 0:
                failure.path += '?' + qs
            failure.errors = errors

            if isinstance(request, ModPythonRequest):
                # prepopulate vars
                request._get_get()
                request._get_post()
                request._get_cookies()
                request._get_files()
                request._get_meta()
                request._get_request()
                request._get_raw_post_data()
                u = request.user
                mp = request._req
                del request._req # get rid of mp_request
                try:
                    req = copy.deepcopy(request)
                except Exception, e:
                    req = "Couldn't stash a copy of the request: %s" % str(e)
                request._req = mp # restore mp_request
            else:
                try:
                    req = copy.deepcopy(request)
                    # remove the stuff we can't serialize
                    del req.META['wsgi.errors']
                    del req.META['wsgi.file_wrapper']
                    del req.META['wsgi.input']
                except Exception, e:
                    # TODO - work out why this happens
                    req = "Couldn't stash a copy of the request: %s" % str(e)

            failure.request = base64.encodestring(cPickle.dumps(req))
            failure.response = base64.encodestring(cPickle.dumps(response))
            failure.method = request.META['REQUEST_METHOD']
            failure.save()
    do_validation = staticmethod(do_validation)
