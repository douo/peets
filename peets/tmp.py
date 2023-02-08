from teletype.components import SelectMany,ChoiceHelper

picker = SelectMany(choices=
                    [ChoiceHelper("Dog", "Dog", mnemonic_style=["green", "bold", "underline"], mnemonic='d'), "bird", "cat", "monkey", "gorilla"])
print("Your Favourite Animals?")
choices = picker.prompt()
breakpoint()
print("Your choices: " + ", ".join(choices))
