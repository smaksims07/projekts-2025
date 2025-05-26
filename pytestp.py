


# veiksmes gadijumi
1. Lietotajs dzeš atgādinajumu ar /delete un tas vairs netiek rādits saraksta
2. Pievienots atgādinājums un tas tiek nosūtīts laikā

#lietošanas scenāriji
1.Lietotājs skatās visus savus atgādinājumus ar "/list"
2.Lietotājs pievieno vairākus atgādinājumus pēc kārtas
3.Lietotājs ievada nepareizu komandu
4. Lietotājs mēģina dzēst neeksistējošu ID

# robežscenāriji

1.Atgādinājums tiek uzstādīts uz pagājušu laiku
2.Ļoti garš atgādinājuma teksts, ja ta bus, vins vai apgriezis vai dos kļūdas pazinojumu.






#vai ir derigs
def test_validate_date_time_correct():
    try:
        datetime.strptime("2025-12-31 15:00", "%Y-%m-%d %H:%M")
        assert True
    except ValueError:
        assert False


#vai eksiste
def test_add_reminder():
    date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    time = '12:00'
    text = 'Testēt matemātiku'
    cursor.execute("INSERT INTO reminders (user_id, text, date, time) VALUES (?, ?, ?, ?)", (123, text, date, time))
    conn.commit()
    cursor.execute("SELECT * FROM reminders WHERE user_id = 123")
    results = cursor.fetchall()
    assert len(results) == 1


#vai ir pazudis
def test_delete_reminder():
    cursor.execute("DELETE FROM reminders WHERE user_id = 123")
    conn.commit()
    cursor.execute("SELECT * FROM reminders WHERE user_id = 123")
    results = cursor.fetchall()
    assert len(results) == 0


#vai nepareiza formāta izraisa kļūdu 
def test_validate_date_time_incorrect():
    try:
        datetime.strptime("nepareizs", "%Y-%m-%d %H:%M")
        assert False
    except ValueError:
        assert True