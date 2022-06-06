from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from core.serializers import NestedDispatchSerializer, DispatchSerializer
from core.models import Dispatch


class DispatchConsumer(AsyncJsonWebsocketConsumer):
    groups = ['test']

    @database_sync_to_async
    def _create_dispatch(self, data):
        serializer = DispatchSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.create(serializer.validated_data)

    @database_sync_to_async
    def _get_dispatch_data(self, dispatch):
        return NestedDispatchSerializer(dispatch).data

    @database_sync_to_async
    def _get_user_group(self, user):
        return user.groups.first().name

    @database_sync_to_async
    def _get_dispatch_ids(self, user):
        user_groups = user.groups.values_list('name', flat=True)
        if 'contractor' in user_groups:
            dispatch_ids = user.contractors.exclude(
                status=Dispatch.COMPLETED
            ).only('id').values_list('id', flat=True)
        else:
            dispatch_ids = user.requestors.exclude(
                status=Dispatch.COMPLETED
            ).only('id').values_list('id', flat=True)
        return map(str, dispatch_ids)

    @database_sync_to_async
    def _update_dispatch(self, data):
        instance = Dispatch.objects.get(id=data.get('id'))
        serializer = DispatchSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.update(instance, serializer.validated_data)

    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            await self.close()
        else:
            user_group = await self._get_user_group(user)
            if user_group == 'contractor':
                await self.channel_layer.group_add(
                    group='contractors',
                    channel=self.channel_name
                )
            for dispatch_id in await self._get_dispatch_ids(user):
                await self.channel_layer.group_add(
                    group=dispatch_id,
                    channel=self.channel_name
                )
            await self.accept()

    async def create_dispatch(self, message):
        data = message.get('data')
        dispatch = await self._create_dispatch(data)
        dispatch_data = await self._get_dispatch_data(dispatch)

        # Send requestor requests to all contractors
        await self.channel_layer.group_send(group='contractors', message={
            'type': 'echo.message',
            'data': dispatch_data
        })

        # Add contractor to dispatch group
        await self.channel_layer.group_add(
            group=f'{dispatch.id}',
            channel=self.channel_name
        )

        await self.send_json({
            'type': 'echo message',
            'data': dispatch_data,
        })

    async def update_dispatch(self, message):
        data = message.get('data')
        dispatch = await self._update_dispatch(data)
        dispatch_id = f'{dispatch.id}'
        dispatch_data = await self._get_dispatch_data(dispatch)

        # Send update to requestor
        await self.channel_layer.group_send(
            group=dispatch_id,
            message={
                'type': 'echo.message',
                'data': dispatch_data,
            }
        )

        # Add driver to the trip group.
        await self.channel_layer.group_add(
            group=dispatch_id,
            channel=self.channel_name
        )

        await self.send_json({
            'type': 'echo.message',
            'data': dispatch_data
        })


    async def disconnect(self, code):
        user = self.scope['user']
        if user.is_anonymous:
            await self.close()
        else:
            user_group = await self._get_user_group(user)
            if user_group == 'contractor':
                await self.channel_layer.group_discard(
                    group='contractors',
                    channel=self.channel_name
                )
            for dispatch_id in await self._get_dispatch_ids(user):
                await self.channel_layer.group_discard(
                    group=dispatch_id,
                    channel=self.channel_name
                )
        await super().disconnect(code)

    async def echo_message(self, message):
        await self.send_json(message)

    async def receive_json(self, content, **kwargs):
        message_type = content.get('type')
        if message_type == 'create.dispatch':
            await self.create_dispatch(content)
        elif message_type == 'echo.message':
            await self.echo_message(content)
        elif message_type == 'update.dispatch':
            await self.update_dispatch(content)
