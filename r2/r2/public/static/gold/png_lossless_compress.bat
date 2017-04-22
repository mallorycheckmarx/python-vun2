for %%x in (*.png) do (
chcp 1250
optipng.exe %%x
)