# Twitter Vaccination Progress Bot
Bot, that reads the current vaccination data inGermany from [RKI's Impfdashboard](https://impfdashboard.de/static/data/germany_vaccinations_timeseries_v2.tsv)
and posts them daily to [Twitter](https://twitter.com/GermanyProgress).

## Build Docker Container
```bash
docker build . -t vacci-bot
docker image save vacci-bot:latest -o vacci-bot.tar
gzip vacci-bot.tar
```
