from guardian.shortcuts import get_objects_for_user


def master_zones(request):
    return {
        "master_zones": get_objects_for_user(
            request.user, "core.has_access", with_superuser=False
        )
    }
