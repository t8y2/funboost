from funboost import boost, BrokerEnum, BoosterParams


@boost(BoosterParams(
    queue_name="demo101_queue",
    broker_kind=BrokerEnum.SQLITE_QUEUE,
))
def add(a, b):
    print(f'{a} + {b} = {a + b}')
    return a + b


if __name__ == '__main__':
    add.push(1, 2)
    add.push(3, 4)
    add.consume()