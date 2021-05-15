from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import Http404
from django.core.mail import send_mail, send_mass_mail
import requests
from .models import Country
from .serializers import CountrySerializer
from deep_translator import GoogleTranslator

c=0

def getcountryinfo(country):
    url='https://vaccovid-coronavirus-vaccine-and-treatment-tracker.p.rapidapi.com/api/npm-covid-data/countries-name-ordered'
    headers = {'x-rapidapi-key': 'be83437380msh3697003aab41f1ap1d95ffjsnad2327d68470','x-rapidapi-host': 'vaccovid-coronavirus-vaccine-and-treatment-tracker.p.rapidapi.com'}
    response = requests.request('GET', url, headers=headers)
    for dictionary in response.json():
        if country.capitalize() == dictionary['Country']:
            return dictionary['ThreeLetterSymbol']

def getstats(country=None):
    global c
    fullstatsurl='https://vaccovid-coronavirus-vaccine-and-treatment-tracker.p.rapidapi.com/api/npm-covid-data/'
    vacurl='https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.json'
    headers = {'x-rapidapi-key': 'be83437380msh3697003aab41f1ap1d95ffjsnad2327d68470','x-rapidapi-host': 'vaccovid-coronavirus-vaccine-and-treatment-tracker.p.rapidapi.com'}
    if country == None:
        response1 = (requests.request('GET', fullstatsurl, headers=headers)).json()
        response2 = (requests.request('GET', vacurl)).json()
        return response1, response2
    else:
        url=f'https://vaccovid-coronavirus-vaccine-and-treatment-tracker.p.rapidapi.com/api/npm-covid-data/country-report-iso-based/{country.capitalize()}/{getcountryinfo(country)}'
        response1 = (requests.request('GET', url, headers=headers)).json()
        response2 = (requests.request('GET', vacurl)).json()
        iso=getcountryinfo(country)
        if iso=='USA':
            c+=1
        for d in response2:
            try:
                if ((d['iso_code']).lower() == iso.lower()) and c==0:
                    response2 = d['data'][-1]
                    break
            except:
                response2=""
        return response1, response2

def getflag(country, style='flat', size='16'):
    sizes=['16','24','32','48','64']
    styles=['flat','shiny']
    
    urlcode = "https://vaccovid-coronavirus-vaccine-and-treatment-tracker.p.rapidapi.com/api/npm-covid-data/countries"

    headers = {
    'x-rapidapi-key': "be83437380msh3697003aab41f1ap1d95ffjsnad2327d68470",
    'x-rapidapi-host': "vaccovid-coronavirus-vaccine-and-treatment-tracker.p.rapidapi.com"
    }

    response = requests.request("GET", urlcode, headers=headers)

    for d in response.json():
        if d['Country']==country.title() or d['Country']==country.upper() or d['Country']==country:
            country_code=d['TwoLetterSymbol'].upper()
            break
    if (size not in sizes) or (style not in styles):
        raise ValueError('Argumento inválido.')
    url=f'https://www.countryflags.io/{country_code}/{style}/{size}.png'
    return url

def initialpopulate():
    fullstats, vacstats = getstats()
    for i in fullstats:
        if i['Population']!='0':
            new_country = Country()
            
            new_country.name = i['Country']
            new_country.flag_url = getflag(i['Country'])
            new_country.flag_url_shiny = getflag(i['Country'], style='shiny')
            new_country.flag_url_big = getflag(i['Country'], size='64')
            new_country.rank = i['rank']
            new_country.population = i['Population']
            
            new_country.total_cases = i['TotalCases']
            new_country.new_cases = i['NewCases']
            new_country.active_cases = i['ActiveCases']
            new_country.cases_1m_pop = i['TotCases_1M_Pop']
            
            new_country.total_deaths = i['TotalDeaths']
            new_country.new_deaths = i['NewDeaths']
            new_country.deaths_1m_pop = i['Deaths_1M_pop']
            
            new_country.total_recovered = i['TotalRecovered']
            new_country.new_recovered = i['NewRecovered']
            
            new_country.infection_risk = i['Infection_Risk']
            new_country.case_fatality_rate = i['Case_Fatality_Rate']
            new_country.recovery_proportion = i['Recovery_Proporation']
            
            a, vacstats2 = getstats(i['Country'])
            try:
                new_country.total_vaccinated = vacstats2['people_vaccinated']
                new_country.vaccinated_proportion = vacstats2['people_vaccinated']/int(i['Population'])
                new_country.vaccinated_1m_pop = (vacstats2['people_vaccinated']*1000000)/int(i['Population'])
                new_country.daily_vaccinated_1m_pop = vacstats2['daily_vaccinations_per_million']
            except:
                new_country.total_vaccinated = 0
                new_country.vaccinated_proportion = 0
                new_country.vaccinated_1m_pop = 0
                new_country.daily_vaccinated_1m_pop = 0
            
            new_country.save()

def index(request):
    if request.method == 'GET':
        try:
            countries=Country.objects.all()
            return render(request, 'stats/index.html', {'countries': countries})
        except:
            raise Http404
    elif request.method == 'POST':
        for country in Country.objects.all():
            if country.name != 'Turkey':
                text=str(country.name)
                translated = GoogleTranslator(source='auto', target='pt').translate(text)
                country.name_pt=translated
            else:
                country.name_pt='Turquia'
            country.save()
        
def country_view(request, country_name):
    country=Country.objects.get(name=country_name)
    return render(request, 'stats/country.html', {'country': country})

def about(request):
    return render(request, 'stats/about.html')

def subscribe(request):
    countries=Country.objects.all()
    return render(request, 'stats/subscribe.html', {'countries': countries})
        
@api_view(['GET', 'POST'])
def api_country(request, country_id):
    try:
        country = Country.objects.get(id=country_id)
    except Country.DoesNotExist:
        raise Http404()
    serialized_country = CountrySerializer(country)
    return Response(serialized_country.data)