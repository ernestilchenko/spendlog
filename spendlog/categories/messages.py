from django.utils.translation import gettext_lazy as _


class CategoryMessages:
    CREATED = _('Category created')
    UPDATED = _('Category saved')
    DELETED = _('Category deleted')
    DUPLICATE = _('This category already exists')


class RuleMessages:
    CREATED = _('Rule saved')
    DELETED = _('Rule deleted')
    DUPLICATE = _('A rule for this merchant already exists')
