import discord

from ada.breadcrumbs import Breadcrumbs
from ada.processor import Processor


class OptimizationCategoryButton(discord.ui.Button):
    def __init__(
            self,
            label: str,
            custom_id: str,
            disabled: bool,
            processor: Processor
    ):
        super().__init__(style=discord.ButtonStyle.primary, label=label, disabled=disabled, custom_id=custom_id, row=0)
        self.__processor = processor

    async def callback(self, interaction: discord.Interaction):
        breadcrumbs = Breadcrumbs.extract(interaction.message.content)
        query = breadcrumbs.primary_query()
        breadcrumbs.set_custom_id(self.custom_id)
        await self.__processor.do_and_edit(query, breadcrumbs, interaction)


class OptimizationView(discord.ui.View):
    def __init__(self, processor: Processor, custom_id: str):
        super().__init__(timeout=None)
        self.__processor = processor

        active_category = custom_id if custom_id else "inputs"
        self._add_categories(active_category, processor)

    def _add_categories(self, active_category: str, processor: Processor):
        for category in ["Inputs", "Outputs", "Recipes", "Buildings", "General"]:
            custom_id = category.lower()
            disabled = custom_id == active_category
            self.add_item(OptimizationCategoryButton(
                label=category,
                custom_id=custom_id,
                disabled=disabled,
                processor=processor
            ))
