from schema import Schema, Or, Optional


def is_valid(data):
    data_schema = Schema(
        {
            Optional('shop'): str,
            Optional('categories'): [
                {
                    'name': str,
                    Optional('id'): Or(int, str)
                }
            ],
            'goods': [
                {
                    'id': Or(int, str),
                    'category': str,
                    'model': str,
                    'name': str,
                    'price': Or(int, float, str),
                    'price_rrc': Or(int, float, str),
                    'quantity': Or(int, str),
                    'parameters': {
                        Optional(str): Or(int, float, str)
                    }
                }
            ]
        }
    )

    try:
        data_schema.validate(data)
    except Exception as e:
        print(e)

    return data_schema.is_valid(data)
