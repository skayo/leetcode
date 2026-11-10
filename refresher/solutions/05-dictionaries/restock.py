# Restock
# Python refresher, Dictionaries
#
# Write `restock(stock)`, which changes the dictionary it's given in place. It
# sells one apple by taking 1 off `stock['apples']`, adds `'kiwis'` with a
# count of 5, and removes `'pears'`. It doesn't need to return anything.
#
#     stock = {'apples': 3, 'pears': 0, 'plums': 7}
#     restock(stock)
#     stock   # {'apples': 2, 'plums': 7, 'kiwis': 5}
#
# Save the file and the refresher runs it, or run it yourself with python3.


def restock(stock):
    stock["apples"] = stock.get("apples") - 1
    stock["kiwis"] = 5
    del stock["pears"]



if __name__ == "__main__":
    # Checks. Running this file runs them.
    stock = {'apples': 3, 'pears': 0, 'plums': 7}
    restock(stock)
    assert stock.get('apples') == 2, f"after restock, stock['apples'] is {stock.get('apples')!r}, and it should be 2"
    assert stock.get('kiwis') == 5, f"after restock, stock['kiwis'] is {stock.get('kiwis')!r}, and it should be 5"
    assert 'pears' not in stock, "after restock, 'pears' is still a key in stock"
    assert stock == {'apples': 2, 'plums': 7, 'kiwis': 5}, f"after restock, stock is {stock!r}"
    print("All checks pass.")
