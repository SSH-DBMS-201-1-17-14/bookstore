
error_code = {
    401: "authorization fail.",
    511: "non exist user id {}",
    512: "exist user id {}",
    513: "non exist store id {}",
    514: "exist store id {}",
    515: "non exist book id {}",
    516: "exist book id {}",
    517: "stock level low, book id {}",
    518: "invalid order id {}",
    519: "not sufficient funds, order id {}",
    520: "no book in the store, store id {}",
    521: "non exist user {} has store {}",
    522: "non exist order {}",
    523: "pay flag not set, haven't pay",
    521: "",
    522: "",
    523: "",
    524: "",
    525: "",
    526: "",
    527: "",
    528: "",
}

# 不存在此用户拥有这个店铺
# def error_non_exist_user_store(user_id,store_id):
#     return 520,error_code[520].format(user_id,store_id)

#  511  (可能遇到的情况：登录时输入此用户名)
def error_non_exist_user_id(user_id):
    return 511, error_code[511].format(user_id)

# 已存在某用户 512 (可能遇到的情况：注册时想要注册此用户名但是已经被占用)
def error_exist_user_id(user_id):
    return 512, error_code[512].format(user_id)

# 不存在某家店铺
def error_non_exist_store_id(store_id):
    return 513, error_code[513].format(store_id)

# 已经存在某家店铺 无法再次进行注册
def error_exist_store_id(store_id):
    return 514, error_code[514].format(store_id)

# 某家店没有卖某本书
def error_non_exist_book_id(book_id):
    return 515,  error_code[515].format(book_id)

# 某店铺某图书已经上架 不可重复上架
def error_exist_book_id(book_id):
    return 516,  error_code[516].format(book_id)

# 库存不足
def error_stock_level_low(book_id):
    return 517, error_code[517].format(book_id)

# 还没有此订单 因为是先进行创建订单，再进行买家和卖家的钱数变动
def error_invalid_order_id(order_id):
    return 518, error_code[518].format(order_id)

# 余额不足
def error_not_sufficient_funds(order_id):
    return 519, error_code[518].format(order_id)

# 在进行交易时，核对处理对象 不能扣错人的钱或者把钱错加到别人的钱上去
def error_authorization_fail():
    return 401, error_code[401]

# 某家店铺未上架过新书
def error_store_book_empty(user_id):
    return 521, error_code[521].format(user_id)

# 自定义错误信息
def error_and_message(code, message):
    return code, message
# error.error_and_message(520,"non exist user {} has store {}".format(user_id,store_id))
