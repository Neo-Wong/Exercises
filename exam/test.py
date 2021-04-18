#! -*- coding: utf-8 -*-
# __file__  : test
# __author__: NeoWong
# __date__  : 2021-04-13 20:10
import time
import hashlib
import pickle

my_cache = {}



def get_data_from_db(keywords):
    print(f"query{keywords}, get from db")
    db_result = f"{keywords} db data"
    return db_result


def cache(n=0):
    def outer(func):
        def inner(*args, **kwargs):
            key = pickle.dumps((func.__name__, args, kwargs))
            key = hashlib.sha1(key).hexdigest()
            print(key)
            if key in my_cache.keys():
                is_pass = 1
                if n:
                    if time.time() - my_cache[key]['time'] < n:
                        is_pass = 1
                    else:
                        is_pass = 0
                    print(is_pass)
                if is_pass:
                    print("ispass")
                    return my_cache[key]["result"]

            res = func(*args, **kwargs)
            my_cache[key] = {
                "result": res,
                "time": time.time()
            }
            return res
        return inner
    return outer


@cache(10)  # func = cache(func)
def query(keywords):
    db_result = get_data_from_db(keywords)



if __name__ == '__main__':
    query('test1')
    print(my_cache)
    time.sleep(10)
    query("test1")