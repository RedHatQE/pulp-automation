import item


class Repo(item.Item):
    path = '/repositories/'
    relevant_data_keys = ['id', 'display_name', 'description', 'notes']
    required_data_keys = ['id']
