import pytest
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework_simplejwt.tokens import AccessToken

from config.routing import application
from core.models import Dispatch

TEST_CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}


@database_sync_to_async
def create_user(
    username,
    password,
    group='requester'):
    # Create user
    user = get_user_model().objects.create_user(
        username=username,
        password=password
    )
    # Create user group
    user_group, _ = Group.objects.get_or_create(name=group)
    user.groups.add(user_group)
    user.save()
    # Create access token
    access = AccessToken.for_user(user)
    return user, access


@database_sync_to_async
def create_dispatch(
    request_location='123 Main Street',
    destination='456 Piney Road',
    status='REQUESTED',
    requestor=None,
    contractor=None
):
    return Dispatch.objects.create(
        request_location=request_location,
        destination=destination,
        status=status,
        requestor=requestor,
        contractor=contractor
    )


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestWebSocket:
    async def test_can_connect_to_server(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        _, access = await create_user(
            'test.user@example.com', 'pAssw0rd'
        )
        communicator = WebsocketCommunicator(
            application=application,
            path=f'/dispatch/?token={access}'
        )
        connected, _ = await communicator.connect()
        assert connected is True
        await communicator.disconnect()

    async def test_can_send_and_receive_messages(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        _, access = await create_user(
            'test.user@example.com', 'pAssw0rd'
        )
        communicator = WebsocketCommunicator(
            application=application,
            path=f'/dispatch/?token={access}'
        )
        await communicator.connect()
        message = {
            'type': 'echo.message',
            'data': 'This is a test message.',
        }
        await communicator.send_json_to(message)
        response = await communicator.receive_json_from()
        assert response == message
        await communicator.disconnect()

    async def test_can_send_and_receive_broadcast_messages(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        _, access = await create_user(
            'test.user@example.com', 'pAssw0rd'
        )
        communicator = WebsocketCommunicator(
            application=application,
            path=f'/dispatch/?token={access}'
        )
        await communicator.connect()
        message = {
            'type': 'echo.message',
            'data': 'This is a test message.',
        }
        channel_layer = get_channel_layer()
        await channel_layer.group_send('test', message=message)
        response = await communicator.receive_json_from()
        assert response == message
        await communicator.disconnect()

    async def test_cannot_connect_to_socket(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        communicator = WebsocketCommunicator(
            application=application,
            path='/dispatch/'
        )
        connected, _ = await communicator.connect()
        assert connected is False
        await communicator.disconnect()

    async def test_join_contractor_pool(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        _, access = await create_user(
            'test.user@example.com', 'pAssw0rd', 'contractor'
        )
        communicator = WebsocketCommunicator(
            application=application,
            path=f'/dispatch/?token={access}'
        )
        await communicator.connect()
        message = {
            'type': 'echo.message',
            'data': 'This is a test message.',
        }
        channel_layer = get_channel_layer()
        await channel_layer.group_send('contractors', message=message)
        response = await communicator.receive_json_from()
        assert response == message
        await communicator.disconnect()

    async def test_request_trip(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        user, access = await create_user(
            'test.user@example.com', 'pAssw0rd', 'requestor'
        )
        communicator = WebsocketCommunicator(
            application=application,
            path=f'/dispatch/?token={access}'
        )
        await communicator.connect()
        await communicator.send_json_to({
            'type': 'create.dispatch',
            'data': {
                'request_location': '123 Main Street',
                'destination': '456 Piney Road',
                'requestor': user.id,
            },
        })
        response = await communicator.receive_json_from()
        response_data = response.get('data')
        assert response_data['id'] is not None
        assert response_data['request_location'] == '123 Main Street'
        assert response_data['destination'] == '456 Piney Road'
        assert response_data['status'] == 'REQUESTED'
        assert response_data['requestor']['username'] == user.username
        assert response_data['contractor'] is None
        await communicator.disconnect()

    async def test_contractor_alerted_on_request(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        # Listen to the 'contractors' group test channel.
        channel_layer = get_channel_layer()
        await channel_layer.group_add(
            group='contractors',
            channel='test_channel'
        )

        user, access = await create_user(
            'test.user@example.com', 'pAssw0rd', 'requestor'
        )
        communicator = WebsocketCommunicator(
            application=application,
            path=f'/dispatch/?token={access}'
        )
        await communicator.connect()

        # Request a dispatch.
        await communicator.send_json_to({
            'type': 'create.dispatch',
            'data': {
                'request_location': '123 Main Street',
                'destination': '456 Piney Road',
                'requestor': user.id,
            },
        })

        # Receive JSON message from server on test channel.
        response = await channel_layer.receive('test_channel')
        response_data = response.get('data')

        assert response_data['id'] is not None
        assert response_data['requestor']['username'] == user.username
        assert response_data['contractor'] is None

        await communicator.disconnect()

    async def test_create_dispatch_group(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        user, access = await create_user(
            'test.user@exmple.com', 'pAss0rd', 'requestor'
        )
        communicator = WebsocketCommunicator(
        application=application,
        path=f'/dispatch/?token={access}'
        )
        await communicator.connect()

        # Send a ride request.
        await communicator.send_json_to({
            'type': 'create.dispatch',
            'data': {
                'request_location': '123 Main Street',
                'destination': '456 Piney Road',
                'requestor': user.id,
            },
        })
        response = await communicator.receive_json_from()
        response_data = response.get('data')

        # Send a message to the trip group.
        message = {
            'type': 'echo.message',
            'data': 'This is a test message.',
        }
        channel_layer = get_channel_layer()
        await channel_layer.group_send(response_data['id'], message=message)

        # Rider receives message.
        response = await communicator.receive_json_from()
        assert response == message

        await communicator.disconnect()

    async def test_join_trip_group_on_connect(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS
        user, access = await create_user(
            'test.user@example.com', 'pAssw0rd', 'requestor'
        )
        dispatch = await create_dispatch(requestor=user)
        communicator = WebsocketCommunicator(
            application=application,
            path=f'/dispatch/?token={access}'
        )
        connected, _ = await communicator.connect()

        # Send a message to the trip group.
        message = {
            'type': 'echo.message',
            'data': 'This is a test message.',
        }
        channel_layer = get_channel_layer()
        await channel_layer.group_send(f'{dispatch.id}', message=message)

        # Rider receives message.
        response = await communicator.receive_json_from()
        assert response == message

        await communicator.disconnect()

    async def test_contractor_can_update_dispatch(self, settings):
        settings.CHANNEL_LAYERS = TEST_CHANNEL_LAYERS

        # Create dispatch request.
        requestor, _ = await create_user(
            'test.rider@example.com', 'pAssw0rd', 'requestor'
        )
        dispatch = await create_dispatch(requestor=requestor)
        dispatch_id = f'{dispatch.id}'

        # Listen for messages as requestor.
        channel_layer = get_channel_layer()
        await channel_layer.group_add(
            group=dispatch_id,
            channel='test_channel'
        )

        # Update dispatch.
        contractor, access = await create_user(
            'test.driver@example.com', 'pAssw0rd', 'contractor'
        )
        communicator = WebsocketCommunicator(
            application=application,
            path=f'/dispatch/?token={access}'
        )
        await communicator.connect()
        message = {
            'type': 'update.dispatch',
            'data': {
                'id': dispatch_id,
                'request_location': dispatch.request_location,
                'destination': dispatch.destination,
                'status': Dispatch.IN_PROGRESS,
                'contractor': contractor.id,
            },
        }
        await communicator.send_json_to(message)

        # Rider receives message.
        response = await channel_layer.receive('test_channel')
        response_data = response.get('data')
        assert response_data['id'] == dispatch_id
        assert response_data['requestor']['username'] == requestor.username
        assert response_data['contractor']['username'] == contractor.username

        await communicator.disconnect()
