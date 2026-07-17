from django import forms


class CalculadoraForm(forms.Form):
    nombre_completo = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': 'Nombre completo'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input', 'placeholder': 'correo@ejemplo.cl'
        })
    )
    telefono = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': '+56 9 1234 5678'
        })
    )

    sueldo_liquido_clp = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': '800.000',
            'inputmode': 'numeric',
            'x-model': 'sueldoDisplay',
            'x-on:input': 'onSueldoInput($event)'
        }),
        label="Mi Sueldo Líquido es de"
    )
    complementa_renta = forms.ChoiceField(
        choices=[('no', 'NO'), ('si', 'SI')],
        required=False,
        widget=forms.RadioSelect(attrs={'x-model': 'complementaRenta'}),
        label="¿Quieres complementar renta?"
    )
    sueldo_2_clp = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input', 'placeholder': '0',
            'inputmode': 'numeric',
            'x-model': 'sueldo2Display',
            'x-on:input': 'onSueldo2Input($event)'
        }),
        label="Sueldo número 2"
    )
    plazo_anios = forms.ChoiceField(
        choices=[(i, f"{i} Años") for i in [5, 10, 15, 20, 25, 30]],
        widget=forms.Select(attrs={
            'class': 'form-input', 'x-model.number': 'plazoAnios',
            'x-on:change': 'calcular()'
        }),
        label="Plazo para pagar mi dpto"
    )
    pie_pct = forms.ChoiceField(
        choices=[(p, f"{p}%") for p in [5, 10, 15, 20, 25, 30]],
        widget=forms.Select(attrs={
            'class': 'form-input', 'x-model.number': 'piePct',
            'x-on:change': 'calcular()'
        }),
        label="Mi ahorro para el pie"
    )
    # Honeypot anti-spam: campo invisible para humanos; si llega con valor,
    # el envío es de un bot y se rechaza.
    sitio_web = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'tabindex': '-1', 'autocomplete': 'off', 'aria-hidden': 'true',
        }),
        label=""
    )
    tasa_interes_id = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-input', 'x-model': 'tasaInteresId',
            'x-on:change': 'onTasaChange()'
        }),
        label="Tasa menor informada"
    )

    def __init__(self, *args, tasas=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tasas:
            self.fields['tasa_interes_id'].choices = [
                (t.id, f"{t.nombre} ({t.porcentaje}%)") for t in tasas
            ]

    def _parse_clp(self, field_name, required=False):
        value = str(self.data.get(field_name, ''))
        value = value.replace('.', '').replace(',', '').strip()
        if not value:
            if required:
                raise forms.ValidationError('Este campo es obligatorio.')
            return 0
        try:
            num = int(value)
        except (ValueError, TypeError):
            raise forms.ValidationError('Ingrese un número válido.')
        if num < 0:
            raise forms.ValidationError('El valor no puede ser negativo.')
        return num

    def clean_sueldo_liquido_clp(self):
        num = self._parse_clp('sueldo_liquido_clp', required=True)
        if num < 1:
            raise forms.ValidationError('Asegúrese de que este valor sea mayor o igual a 1.')
        return num

    def clean_sueldo_2_clp(self):
        return self._parse_clp('sueldo_2_clp', required=False)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('sitio_web'):
            raise forms.ValidationError(
                'No pudimos validar tu envío. Recarga la página e intenta de nuevo.')
        # Si no complementa renta, ignorar el sueldo 2.
        if cleaned_data.get('complementa_renta') != 'si':
            cleaned_data['sueldo_2_clp'] = 0
        return cleaned_data
