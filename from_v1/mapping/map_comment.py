from mapping.map_model import MapModel
import landmatrix.models
import editor.models

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'


class MapComment(MapModel):
    old_class = editor.models.Comment
    new_class = landmatrix.models.Comment
    attributes = {
        'activity_attribute_group': 'fk_activity_attribute_group',
        'stakeholder_attribute_group': 'fk_stakeholder_attribute_group'
    }
