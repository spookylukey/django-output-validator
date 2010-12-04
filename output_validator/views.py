from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from output_validator.models import ValidationFailure


def bulkdelete(request):
    if request.POST:
        postkeys = request.POST.keys()
        if 'deleteall' in postkeys:
            ValidationFailure.objects.all().delete()
        elif 'deleteselected' in postkeys:
            for k in postkeys:
                if k.startswith('deleteitem'):
                    k = k[len('deleteitem'):]
                    try:
                        vf = ValidationFailure.objects.get(id=k)
                        vf.delete()
                    except ValidationFailure.DoesNotExist:
                        pass

    return HttpResponseRedirect(reverse('output_validator.list'))


def delete(request, pk):
    if request.POST:
        try:
            vf = ValidationFailure.objects.get(pk=pk)
            vf.delete()
        except ValidationFailure.DoesNotExist:
            pass
    return HttpResponseRedirect(reverse('output_validator.list'))

