import item

class EventListener(item.Item):
    relevant_data_keys = ['id', 'notifier_type_id', 'notifier_config', 'event_types']
    required_data_keys = []
    path = '/events/'

    @classmethod
    def http(cls, url, event_types=['repo.sync.finish', 'repo.publish.finish']):
        '''construct an http event listener'''
        data = {
            'notifier_type_id': 'http',
            'notifier_config': {
                'url': url
            },
            'event_types': event_types
        }
        return cls(data)
