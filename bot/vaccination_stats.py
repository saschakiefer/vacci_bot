import datetime
import logging

import pandas as pd

logger = logging.getLogger()


class VaccinationStats:
    DATA_SOURCE = (
        "https://impfdashboard.de/static/data/germany_vaccinations_timeseries_v2.tsv"
    )

    POPULATION = 83190556

    def __init__(self):
        df = pd.read_csv(VaccinationStats.DATA_SOURCE, sep="\t", header=0)

        logger.info("Data loaded")

        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
        self.date = pd.Timestamp(df.tail(1)["date"].values[0]).to_pydatetime()
        logger.info(f"Current dataset date is {self.date}")

        self.vacc_cumulated = df.tail(1)["dosen_kumulativ"].values[0]
        self.vacc_both = df.tail(1)["personen_voll_kumulativ"].values[0]
        self.vacc_first = df.tail(1)["personen_erst_kumulativ"].values[0]

        self.vacc_quote_first = self.vacc_first / VaccinationStats.POPULATION
        if self.vacc_quote_first > 1:
            self.vacc_quote_first = 1

        # If we reach 70% switch to 100% as target
        self.target_quote = 0.7
        if self.vacc_quote_first > 0.7:
            self.target_quote = 1

        self.vacc_quote_complete = self.vacc_both / VaccinationStats.POPULATION
        if self.vacc_quote_complete > 1:
            self.vacc_quote_complete = 1

        self.vacc_median = df.tail(7)["dosen_differenz_zum_vortag"].mean()

        self.people_to_go = (
            VaccinationStats.POPULATION * self.target_quote - self.vacc_first
        )
        self.days_to_go = int(round(self.people_to_go / self.vacc_median))

        self.target_date = datetime.datetime.today() + datetime.timedelta(
            days=self.days_to_go
        )
