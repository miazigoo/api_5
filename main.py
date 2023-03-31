import os
import requests
from dotenv import load_dotenv
from terminaltables import SingleTable

def get_hh_vacancies(programming_lang):
    """Получение списка вакансий по языку программирования"""
    id_moscow_city = 1
    search_days_period = 30
    page = 0
    url = 'https://api.hh.ru/vacancies/'
    params = {
        'text': programming_lang,
        'area': id_moscow_city,
        'period': search_days_period,
        'page': page
    }
    count = 0
    vacancies = []

    while True:
        page_response = requests.get(url, params=params)
        page_response.raise_for_status()
        vacancies_and_count = page_response.json()
        if not vacancies_and_count:
            break
        vacancies.append(vacancies_and_count)
        count = vacancies_and_count['found']
        page += 1

    return count, vacancies


def predict_rub_salary_hh(vacancy):
    """Получение полей зарплаты "От" и "До" """
    try:
        vacancy_salary = vacancy['salary']
        currency = vacancy_salary['currency'] or None
        salary_from = vacancy_salary['from'] or None
        salary_to = vacancy_salary['to'] or None
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


def calculate_languages_statistics_hh(vacancies_hh):
    """Подсчет по яз. средней з/п и кол-во обработанных вакансий"""
    salaries = []
    for vacancies in vacancies_hh:
        for vacancy in vacancies['items']:
            salary_from, salary_to = predict_rub_salary_hh(vacancy)
            rub_salary = predict_salary(salary_from, salary_to)
            if rub_salary:
                salaries.append(int(rub_salary))
    try:
        average_salary_hh = int(sum(salaries) / len(salaries))
    except ZeroDivisionError:
        average_salary_hh = 0
    vacancies_processed_hh = len(salaries)

    return vacancies_processed_hh, average_salary_hh


def get_sj_vacancies(programming_lang, sj_secret_key):
    """Получение списка вакансий по языку программирования"""
    page = 0
    pages = 5
    vacancies = []
    programming_group = 48
    count_vacancies_on_page = 100
    search_by_position = {'int': 1}
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
            'catalogues': programming_group,
            'count': count_vacancies_on_page,
            'keywords': [search_by_position],
            'page': page,
        }

        response = requests.get(url=url, params=params, headers=headers)
        response.raise_for_status()
        vacancies_page = response.json()['objects']
        vacancies.append(vacancies_page)
        page += 1

        if not vacancies_page:
            break

    return vacancies


def predict_rub_salary_sj(vacancy):
    """Получение полей зарплаты "От" и "До" """
    try:
        salary_from = vacancy['payment_from'] or None
        salary_to = vacancy['payment_to']
        if salary_from and salary_to == 0:
            salary_from = None
            salary_to = None
    except TypeError:
        salary_from = None
        salary_to = None

    return salary_from, salary_to


def calculate_languages_statistics_sj(sj_vacancies):
    """Подсчет по яз. средней з/п, кол-во вакансий и кол-во обработанных вакансий"""
    salaries = []
    vacancies_count_sj = 0
    for vacancies in sj_vacancies:
        for vacancy in vacancies:
            vacancies_count_sj += 1
            salary_from, salary_to = predict_rub_salary_hh(vacancy)
            rub_salary = predict_salary(salary_from, salary_to)
            if rub_salary:
                salaries.append(int(rub_salary))
    vacancies_processed_sj = len(salaries)
    try:
        average_salary_sj = int(sum(salaries) / len(salaries))
    except ZeroDivisionError:
        average_salary_sj = 0

    return vacancies_processed_sj, average_salary_sj, vacancies_count_sj


def view_table(table,title):
    """ view table """
    table_instance = SingleTable(table, title)
    table_instance.justify_columns[2] = 'right'
    return table_instance.table


def main():
    load_dotenv()
    sj_secret_key = os.environ['SUPERJOB_SECRET_KEY']
    programming_languages = ('JavaScript', 'Java', 'Python', 'Ruby', 'PHP', 'C++', 'C#', 'Go', 'C')
    table_sj = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'],
    ]
    table_hh = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'],
    ]

    for programming_lang in programming_languages:
        print(f'Обрабатываются вакансии по языку программирования: {programming_lang}')
        """ HeadHunter """
        vacancies_count_hh, vacancies_hh = get_hh_vacancies(programming_lang)
        vacancies_processed_hh, average_salary_hh = calculate_languages_statistics_hh(vacancies_hh)
        table_hh.append(
            [programming_lang,
             vacancies_count_hh,
             vacancies_processed_hh,
             average_salary_hh
             ])

        """ SuperJob """
        sj_vacancies = get_sj_vacancies(programming_lang, sj_secret_key)
        vacancies_processed_sj, average_salary_sj, vacancies_count_sj = calculate_languages_statistics_sj(sj_vacancies)
        table_sj.append(
            [programming_lang,
             vacancies_count_sj,
             vacancies_processed_sj,
             average_salary_sj
             ])

    """ view table """
    title_hh = 'HeadHunter Moscow'
    title_sj = 'SuperJob Moscow'
    view_table_hh = view_table(table_hh, title_hh)
    view_table_sj = view_table(table_sj, title_sj)
    print(view_table_hh, '\n', '\n', view_table_sj)


if __name__ == '__main__':
    main()


