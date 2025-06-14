from mods.firemod import init_db, client, to_dict_all, has_key, get_contract

db: client = init_db()
tolls: list[dict] = to_dict_all(db.collection('Toll').get())

for toll in tolls.copy():
    if toll['paid'] or not has_key(toll, 'nickname'):
        tolls.remove(toll)

for toll in tolls:
    print('move toll', toll['ID'])
    contract = get_contract(db, toll['nickname'])
    db.collection('Pay_contract').add({
        'nickname': toll['nickname'],
        'ContractName': contract['ContractName'],
        'sum': toll['sum'],
        'name_pay': 'Toll',
        'category': 'toll',
        'expense': True,
        'income': False,
        'delete': False,
        'owner': True,
        'date': toll['date'],
        'user': 'python'
    })