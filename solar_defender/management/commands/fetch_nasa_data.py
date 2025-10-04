from django.core.management.base import BaseCommand
from solar_defender.services import NASAService

class Command(BaseCommand):
    help = 'Fetch solar flare data from NASA API'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to fetch data for'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        
        self.stdout.write(self.style.WARNING(f'Fetching NASA data for last {days} days...'))
        
        nasa_service = NASAService()
        flares = nasa_service.fetch_and_save_flares()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully fetched {len(flares)} solar flares')
        )
        
        for flare in flares:
            self.stdout.write(
                f'  - {flare.class_type} at {flare.begin_time} '
                f'(Simulation: {flare.is_simulation})'
            )


