from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError


class Command(createsuperuser.Command):
    help = "Create a superuser, and allow password to be provided"

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--pass",
            dest="password",
            default=None,
            help="Specifies the password for the superuser.",
        )
        parser.add_argument(
            "--email_address",
            dest="email",
            default=None,
            help="Specifies the email for the superuser.",
        )

    def handle(self, *args, **options):
        password = options.get("password")
        email = options.get("email")
        database = options.get("database")

        if not password:
            raise CommandError("--pass is required")
        if not email:
            raise CommandError("--email_address is required")

        exists = (
            self.UserModel._default_manager.db_manager(database)
            .filter(email=email)
            .exists()
        )
        if exists:
            self.stdout.write("User exists, exiting normally.")
            return

        super(Command, self).handle(*args, **options)

        user = self.UserModel._default_manager.db_manager(database).get(
            email=email
        )
        user.set_password(password)
        user.save()
