from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.exceptions import APIException

from comment.models import Comment


class CommentErrorValidation(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Bad Request'

    def __init__(self, detail=None, status_code=None):
        if status_code:
            self.status_code = status_code
        if not detail:
            detail = self.default_detail
        self.detail = detail


class BaseValidatorMixin:
    api = False
    app_name = None
    model_name = None
    model_id = None
    parent_id = None
    error = None

    def dispatch(self, request, *args, **kwargs):
        """
            let rest framework handle the exception to choose the right renderer
            validate method shall be called in the derived API class
        """
        if self.api:
            return super().dispatch(request, *args, **kwargs)
        try:
            self.validate(request)
        except CommentErrorValidation as exc:
            return JsonResponse({'type': 'error', 'detail': exc.detail}, status=400)
        return super().dispatch(request, *args, **kwargs)

    def validate(self, request):
        self.app_name = request.GET.get("app_name") or request.POST.get("app_name")
        self.model_name = request.GET.get("model_name") or request.POST.get("model_name")
        self.model_id = request.GET.get("model_id") or request.POST.get("model_id")
        self.parent_id = request.GET.get("parent_id") or request.POST.get("parent_id")


class ContentTypeValidator(BaseValidatorMixin):
    def validate(self, request):
        super().validate(request)
        if not self.model_name:
            self.error = _("model name must be provided")
            raise CommentErrorValidation(self.error)
        if not self.model_id:
            self.error = _("model id must be provided")
            raise CommentErrorValidation(self.error)
        if not self.app_name:
            self.error = _('app name must be provided')
            raise CommentErrorValidation(self.error)

        cause = 'app'
        try:
            ContentType.objects.get(app_label=self.app_name)
            cause = 'model'
            model_name = self.model_name.lower()
            ct = ContentType.objects.get(model=model_name).model_class()
            model_class = ct.objects.filter(id=self.model_id)
            if not model_class.exists() and model_class.count() != 1:
                self.error = _(f'{self.model_id} is NOT a valid model id for the model {self.model_name}')
                raise CommentErrorValidation(self.error)
        except ContentType.DoesNotExist:
            if cause == 'app':
                self.error = _(f'{self.app_name} is NOT a valid app name')
                raise CommentErrorValidation(self.error)
            else:
                self.error = _(f'{self.model_name} is NOT a valid model name')
                raise CommentErrorValidation(self.error)
        except ValueError:
            self.error = _(f'model id must be an integer, {self.model_id} is NOT')
            raise CommentErrorValidation(self.error)


class ParentIdValidator(BaseValidatorMixin):
    def validate(self, request):
        super().validate(request)
        if not self.parent_id or self.parent_id == '0':
            return
        try:
            Comment.objects.get(id=self.parent_id, object_id=self.model_id)
        except Comment.DoesNotExist:
            self.error = _(
                f'{self.parent_id} is NOT a valid id for a parent comment or '
                'the parent comment does NOT belong to the provided model object'
            )
            raise CommentErrorValidation(self.error)
        except ValueError:
            self.error = _(f'the parent id must be an integer, {self.parent_id} is NOT')
            raise CommentErrorValidation(self.error)


class ValidatorMixin(ContentTypeValidator, ParentIdValidator):
    pass
