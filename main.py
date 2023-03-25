import os
import requests
from dotenv import load_dotenv
from terminaltables import SingleTable

def get_hh_vacancies(programming_lang):
    """Получение списка вакансий по языку программирования"""
    url = 'https://api.hh.ru/vacancies/'
    params = {
        'text': programming_lang,
        'area': 1,
        'period': 30,
        'only_with_salary': True,
    }

    response = requests.get(url=url, params=params)
    response.raise_for_status()
    count = response.json()['found']
    pages = response.json()['pages']
    page = response.json()['page']
    vacancies = []

    while page < pages:
        params_page = {
            'text': programming_lang,  # ('JavaScript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'C#', 'Go', 'C')
            'area': 1,
            'period': 30,
            'only_with_salary': True,
            'page': page,
        }
        page_response = requests.get(url, params=params_page)
        page_response.raise_for_status()
        vacancies.append(page_response.json())
        page += 1

    return count, vacancies


def predict_rub_salary_hh(vacanci):
    """Получение полей зарплаты "От" и "До" """
    try:
        vacanci_salary = vacanci['salary']
        currency = vacanci_salary['currency']
        salary_from = vacanci_salary['from'] or None
        salary_to = vacanci_salary['to'] or None
        if not currency == 'RUR':
            salary_from = None
            salary_to = None
    except TypeError and KeyError:
        salary_from = None
        salary_to = None

    return salary_from, salary_to


def predict_salary(salary_from, salary_to):
    """Расчет средней зарплаты"""
    salary = None
    if salary_from and salary_to:
        salary = (salary_to + salary_from) / 2
    if salary_to and not salary_from:
        salary = salary_to * 0.8
    if salary_from and not salary_to:
        salary = salary_from * 1.2
    return salary


def calculate_languages_statistics_hh(
        vacancies_dict, programming_lang, vacancies_count, lang_statistics_hh):
    """Подсчет по яз. средней з/п, кол-во вакансий и кол-во обработанных вакансий"""
    salary = []
    for vacancies in vacancies_dict:
        for vacanci in vacancies['items']:
            salary_from, salary_to = predict_rub_salary_hh(vacanci)
            rub_salary = predict_salary(salary_from, salary_to)
            if rub_salary:
                salary.append(int(rub_salary))
        try:
            average_salary = sum(salary) / len(salary)
        except ZeroDivisionError:
            average_salary = 0
        lang_statistics_hh[programming_lang] = {
            "vacancies_found": vacancies_count,
            "vacancies_processed": len(salary),
            "average_salary": int(average_salary),
        }
    return lang_statistics_hh


def get_sj_vacancies(programming_lang, sj_secret_key):
    """Получение списка вакансий по языку программирования"""
    page = 0
    pages = 5
    vacancies = []
    while page < pages:
        url = 'https://api.superjob.ru/2.0/vacancies/get/'
        headers = {
            'Host': 'api.superjob.ru',
            'X-Api-App-Id': sj_secret_key,
            'Authorization': 'Bearer r.000000010000001.example.access_token',
        }
        params = {
            'keyword': programming_lang,
            'town': 'Москва',
            'catalogues': 48,
            'count': 100,
            'keywords': [{'int': 1}],
            'page': page,
        }

        response = requests.get(url=url, params=params, headers=headers)
        response.raise_for_status()
        vacancies_page = response.json()['objects']
        vacancies.append(vacancies_page)
        page += 1

        if len(vacancies_page) == 0:
            break

    return vacancies



def predict_rub_salary_sj(vacanci):
    """Получение полей зарплаты "От" и "До" """
    try:
        salary_from = vacanci['payment_from'] or None
        salary_to = vacanci['payment_to']
        if salary_from and salary_to == 0:
            salary_from = None
            salary_to = None
    except TypeError:
        salary_from = None
        salary_to = None

    return salary_from, salary_to


def calculate_languages_statistics_sj(sj_vacancies_dict, lang_statistics_sj, programming_lang):
    """Подсчет по яз. средней з/п, кол-во вакансий и кол-во обработанных вакансий"""
    salary = []
    vacancies_count = 0
    for vacancies in sj_vacancies_dict:
        for vacanci in  vacancies:
            vacancies_count += 1
            salary_from, salary_to = predict_rub_salary_hh(vacanci)
            rub_salary = predict_salary(salary_from, salary_to)
            if rub_salary:
                salary.append(int(rub_salary))
        try:
            average_salary = sum(salary) / len(salary)
        except ZeroDivisionError:
            average_salary = 0

        lang_statistics_sj[programming_lang] = {
            "vacancies_found": vacancies_count,
            "vacancies_processed": len(salary),
            "average_salary": int(average_salary),
        }
    return lang_statistics_sj


def table_superjob(table_sj):
    """table SuperJob"""
    title_sj = 'SuperJob Moscow'
    table_instance_sj = SingleTable(table_sj, title_sj)
    table_instance_sj.justify_columns[2] = 'right'
    return table_instance_sj.table


def table_headhunter(table_hh):
    """table HeadHunter"""
    title_hh = 'HeadHunter Moscow'
    table_instance_hh = SingleTable(table_hh, title_hh)
    table_instance_hh.justify_columns[2] = 'right'
    return table_instance_hh.table


def main():
    load_dotenv()
    sj_secret_key = os.environ['SUPERJOB_SECRET_KEY']
    programming_lang_list = ('JavaScript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'C#', 'Go', 'C')
    lang_statistics_hh = {}
    lang_statistics_sj = {}
    table_sj = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'],
    ]
    table_hh = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'],
    ]

    for programming_lang in programming_lang_list:
        print(f'Обрабатываются вакансии по языку программирования: {programming_lang}')
        """ HeadHunter """
        vacancies_count_hh, vacancies_dict_hh = get_hh_vacancies(programming_lang)
        languages_statistics = calculate_languages_statistics_hh(
            vacancies_dict_hh, programming_lang, vacancies_count_hh, lang_statistics_hh)
        table_hh.append(
            [programming_lang,
             lang_statistics_hh[programming_lang]["vacancies_found"],
             lang_statistics_hh[programming_lang]["vacancies_processed"],
             lang_statistics_hh[programming_lang]["average_salary"]
             ])

        """ SuperJob """
        sj_vacancies_dict = get_sj_vacancies(programming_lang, sj_secret_key)
        lang_statistics = calculate_languages_statistics_sj(
            sj_vacancies_dict, lang_statistics_sj, programming_lang)
        table_sj.append(
            [programming_lang,
             lang_statistics_sj[programming_lang]["vacancies_found"],
             lang_statistics_sj[programming_lang]["vacancies_processed"],
             lang_statistics_sj[programming_lang]["average_salary"]
             ])

    view_table_hh = table_headhunter(table_hh)
    view_table_sj = table_superjob(table_sj)
    print(view_table_hh, '\n', '\n', view_table_sj)


if __name__ == '__main__':
    main()
    pass

