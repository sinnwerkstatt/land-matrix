from django.db import models

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

class Stakeholder(models.Model):

    id = models.AutoField(primary_key=True)
    stakeholder_identifier = models.CharField(max_length=255, null=False)
    fk_changeset = models.IntegerField()
    fk_status = models.IntegerField()
    version = models.IntegerField()
    reliability = models.IntegerField()
    previous_version = models.IntegerField()
    timestamp_entry = models.DateTimeField()
    fk_user_review = models.IntegerField()
    timestamp_review = models.DateTimeField()
    comment_review = models.CharField(max_length=255)

    class Meta:
        app_label = 'from_v1'
        db_table = "stakeholders"

    @property
    def identifier(self):
        return self.stakeholder_identifier

    def __repr__(self):
        return (
            '<Stakeholder> id [ %s ] | stakeholder_identifier [ %s ] | '
            'fk_changeset [ %s ] | fk_status [ %s ] | version [ %s ] | '
            'previous_version [ %s ] | fk_user_review [ %s ] | '
            'timestamp_review [ %s ] | comment_review [ %s ]' % (
                self.id, self.stakeholder_identifier, self.fk_changeset,
                self.fk_status, self.version, self.previous_version,
                self.fk_user_review, self.timestamp_review,
                self.comment_review))

    def get_comments(self):
        return DBSession.query(Comment).\
            filter(Comment.stakeholder_identifier ==
                   self.stakeholder_identifier).\
            all()

