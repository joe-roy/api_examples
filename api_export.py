import requests
import pandas as pd
from io import StringIO
import configparser


def get_cookie(username, password):
    # Input:
    # username: username from the config.ini file
    # password: password form the config.ini file
    #
    # Output: returns the .SharedCookie value needed to export query results

    # API authentication url
    url = "https://survey.asee.org/api/token"

    # Set username and password for POST query
    payload = "username={username}&password={password}".format(username=username, password=password)
    # Set the content type for the POST query
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Run the POST query
    response = requests.request("POST", url, headers=headers, data=payload)

    # Save the cookie and return its value
    cookie_dict = response.cookies.get_dict()
    cookie = ".SharedCookie=" + cookie_dict['.SharedCookie']
    return cookie


class AuthenticationException(Exception):
    pass


class FailedQueryException(Exception):
    pass


def run_export(model_id, query_id, cookie, output):
    # Input:
    # model_id: id of the model being used to run the query
    # query_id: id of the desired query being run
    # cookie: .SharedCookie value from the config.ini file
    # output: output file location
    #
    # Output: saves a .csv file containing the contents of the query results

    # API url for query exports
    url = "https://newedms.asee.org/api/reports/models/{model_id}/queries/{query_id}/export/csv".format(
        model_id=model_id, query_id=query_id)

    # No payload needed
    payload = {}

    # Set the cookie value
    headers = {'Cookie': cookie}

    # Run the POST query

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 403:
        raise AuthenticationException()
    elif response.status_code != 200:
        raise FailedQueryException()



    # Format the results as a Pandas DataFrame
    df = pd.read_csv(StringIO(response.text))
    # Save the results to a .csv file in the 'output' file location
    df.to_csv(output, index=False)


if __name__ == '__main__':
    # Read in config file
    config = configparser.ConfigParser()
    config.read('config.ini')
    # Get username and password for authentication purposes
    username = config['CREDENTIALS']['username']
    password = config['CREDENTIALS']['password']
    # Get output location for the results file
    output_path = config['FILES']['output']
    # Get last used cookie value
    cookie = config['COOKIES']['cookie']
    # Ask user for model_id
    model_id = input("Enter your model_id: ")
    # Ask user for query_id
    query_id = input("Enter your query_id: ")
    # Ask user for filename
    output_file = input("Enter your output filename: ")

    output = output_path + output_file

    # Preset model_id
    # model_id = '298ffe00-c24b-401c-9449-25003ddc52a0'
    # Preset query_id
    # query_id = '6a0a707d-ba7a-472e-bafd-c1563f247e66'

    # Try to use previous cookie to run the export function
    try:
        print("Exporting results for model_id: ", model_id, "and query_id: ", query_id)
        run_export(model_id, query_id, cookie, output)
        print("Export complete. Results can be found in ", output)
        exit()

    # If the cookie has expired:
    except AuthenticationException:
        # Get a new cookie using the username and password provided
        print("Old cookie has expired retrieving new one")
        cookie = get_cookie(username, password)
        # Write new cookie value to the config file
        config.set('COOKIES', 'cookie', cookie)
        with open('config.ini', 'w') as f:
            config.write(f)

    except FailedQueryException:
        print("There was an error in your query please check that your model_id and query_id are correct.")
        raise

    # Run the export function with the new cookie
    print("Exporting results for model_id: ", model_id, "and query_id: ", query_id)
    run_export(model_id, query_id, cookie, output)
    print("Export complete. Results can be found in ", output)