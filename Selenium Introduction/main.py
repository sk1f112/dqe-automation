
import os
import csv
import time

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
    StaleElementReferenceException,
)


class SeleniumWebDriverContextManager:
    def __init__(self):
        self.driver = None

    def __enter__(self) -> WebDriver:
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()
        return self.driver

    def __exit__(self, exc_type, exc_value, traceback):
        if self.driver is not None:
            self.driver.quit()
        return False


def extract_table_to_csv(
    driver,
    output_file="Selenium Introduction/CSV/table.csv",
):
    wait = WebDriverWait(driver, 10)

    try:
        wait.until(
            EC.visibility_of_element_located(
                (By.CLASS_NAME, "table")
            )
        )

        table = driver.find_element(By.CLASS_NAME, "table")

        wait.until(
            lambda d: len(
                table.find_elements(By.CLASS_NAME, "y-column")
            ) > 0
        )

        columns = table.find_elements(
            By.CLASS_NAME, "y-column"
        )

        headers = []
        column_values = []

        for column in columns:
            header_element = column.find_element(
                By.ID, "header"
            )
            header = header_element.text.strip()
            headers.append(header)

            cells = column.find_elements(
                By.CLASS_NAME, "cell-text"
            )

            values = [
                cell.text.strip()
                for cell in cells
                if cell.text.strip() != header
            ]

            column_values.append(values)

        if not headers:
            raise ValueError("No table headers found.")

        max_rows = max(
            (len(values) for values in column_values),
            default=0,
        )

        table_data = [headers]

        for i in range(max_rows):
            row = [
                values[i] if i < len(values) else ""
                for values in column_values
            ]
            table_data.append(row)

        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

        with open(
            output_file,
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(table_data)

        print(f"Table CSV saved to: {os.path.abspath(output_file)}")
        print(f"Columns: {len(headers)}")
        print(f"Data rows: {max_rows}")

    except TimeoutException:
        print("Error: Table did not become visible within 10 seconds.")
    except NoSuchElementException as error:
        print(f"Error: Table element was not found: {error}")
    except (OSError, ValueError, WebDriverException) as error:
        print(f"Error extracting table: {error}")


def extract_doughnut_data(
    driver,
    output_file,
    category_header="Facility Type",
    value_header="Min Average Time Spent",
):
    wait = WebDriverWait(driver, 10)

    try:
        wait.until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "pielayer")
            )
        )

        doughnut = driver.find_element(
            By.CLASS_NAME, "pielayer"
        )

        labels = doughnut.find_elements(
            By.CSS_SELECTOR,
            "text.slicetext[data-notex='1']",
        )

        rows = [[category_header, value_header]]

        for label in labels:
            tspans = label.find_elements(By.TAG_NAME, "tspan")

            if len(tspans) >= 2:
                category = tspans[0].text.strip()
                value = tspans[1].text.strip()

                if category and value:
                    rows.append([category, value])

        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

        with open(
            output_file,
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(rows)

        print(f"Doughnut CSV saved to: {os.path.abspath(output_file)}")
        print(f"Categories extracted: {len(rows) - 1}")

    except TimeoutException:
        print("Error: Doughnut chart did not load in time.")
    except NoSuchElementException as error:
        print(f"Error: Doughnut chart element not found: {error}")
    except (OSError, WebDriverException) as error:
        print(f"Error extracting doughnut data: {error}")


def process_doughnut_chart(driver):
    output_dir = "Selenium Introduction/CSV"
    screenshots_dir = "Selenium Introduction/screenshots"

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(screenshots_dir, exist_ok=True)

    wait = WebDriverWait(driver, 10)

    try:
        wait.until(
            EC.visibility_of_element_located(
                (By.CLASS_NAME, "pielayer")
            )
        )

        # Initial unfiltered chart: screenshot0 and doughnut0.csv
        driver.save_screenshot(
            os.path.join(screenshots_dir, "screenshot0.png")
        )
        extract_doughnut_data(
            driver,
            os.path.join(output_dir, "doughnut0.csv"),
        )

        filter_selector = "g.legend g.traces"
        
        initial_filters = driver.find_elements(
            By.CSS_SELECTOR, filter_selector
        )

        if not initial_filters:
            print(
                "No filter elements found. Update filter_selector "
                "to match the actual report HTML."
            )
            return

        filter_count = len(initial_filters)

        for index in range(filter_count):
            try:
                filters = wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, filter_selector)
                    )
                )

                if index >= len(filters):
                    break

                filter_element = filters[index]

                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    filter_element,
                )

                wait.until(
                    lambda d: filter_element.is_displayed()
                    and filter_element.is_enabled()
                )

                filter_element.click()

                # Wait for the chart layer to remain available after click.
                wait.until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "pielayer")
                    )
                )
                time.sleep(0.5)

                number = index + 1

                driver.save_screenshot(
                    os.path.join(
                        screenshots_dir,
                        f"screenshot{number}.png",
                    )
                )

                extract_doughnut_data(
                    driver,
                    os.path.join(
                        output_dir,
                        f"doughnut{number}.csv",
                    ),
                )

            except (
                TimeoutException,
                NoSuchElementException,
                StaleElementReferenceException,
                WebDriverException,
            ) as error:
                print(f"Could not apply filter {index + 1}: {error}")

    except (TimeoutException, WebDriverException) as error:
        print(f"Unable to process doughnut chart: {error}")


if __name__ == "__main__":
    with SeleniumWebDriverContextManager() as driver:
        file_path = os.path.abspath(
            r"C:\Users\vladyslav_ostapenko\Desktop\dqe-automation"
            r"\Selenium Introduction\report.html"
        )

        driver.get("file:///" + file_path.replace("\\", "/"))

        # Export the table.
        extract_table_to_csv(
            driver,
            "Selenium Introduction/CSV/table.csv",
        )

        # Export the doughnut chart and its filter states.
        process_doughnut_chart(driver)
