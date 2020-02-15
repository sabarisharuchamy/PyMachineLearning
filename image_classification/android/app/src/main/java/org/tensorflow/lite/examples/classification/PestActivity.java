package org.tensorflow.lite.examples.classification;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Spinner;
import android.widget.TextView;

public class PestActivity extends AppCompatActivity implements
        AdapterView.OnItemSelectedListener {
private TextView textView1,textView2,textView3,textView4;
    String disease;
    String[] languages;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.pest_suggestion);
        languages=getResources().getStringArray(R.array.languages);
        Spinner spin = (Spinner) findViewById(R.id.spinner);
        spin.setOnItemSelectedListener(this);
        ArrayAdapter aa = new ArrayAdapter(this,android.R.layout.simple_spinner_item,languages);
        aa.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spin.setAdapter(aa);
        //int spinnerPosition = aa.getPosition("ENGLISH");

        //spin.setSelection(spinnerPosition);
        Bundle extras = getIntent().getExtras();
        disease = extras.getString("disease");
        textView1 = findViewById(R.id.textView);
        textView2 = findViewById(R.id.textView2);
        textView3 = findViewById(R.id.textView3);
        textView4 = findViewById(R.id.textView4);

    }

    @Override
    public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
if (languages[position].equals("ENGLISH")){
    textView4.setText(R.string.nutrientManagement);
    switch (disease){
        case "bacterialSpot":
            textView1.setText("Bacterial Spot");
            textView2.setText(R.string.bacterialSpot1);
            textView3.setText(R.string.bacterialSpot2);
            break;
        case "lateblight":
            textView1.setText("Late Blight");
            textView2.setText(R.string.lateBlight1);
            textView3.setText(R.string.lateBlight2);

            break;
        case "septoriaLeafSpot":
            textView1.setText("Septoria Leaf Spot");
            textView2.setText(R.string.septoriaLeafSpot1);
            textView3.setText(R.string.septoriaLeafSpot2);
            break;
        case "tomato_mosaic":
            textView1.setText("Tomato Mosaic");
            textView2.setText(R.string.tomatoMosaic1);
            textView3.setText(R.string.tomatoMosaic2);
            break;
        case "yellowcurved":
            textView1.setText("Yellow Leaf Curl");
            textView2.setText(R.string.yellowLeafCurl1);
            textView3.setText(R.string.yellowLeafCurl2);
            break;
        default:
    }
}else{
    textView4.setText(R.string.nutrientManagement2);
    switch (disease){
        case "bacterialSpot":
            textView1.setText("பாக்டீரியா இலைப்புள்ளி");
            textView2.setText(R.string.bacterialSpot3);
            textView3.setText(R.string.bacterialSpot4);
            break;
        case "lateblight":
            textView1.setText("பின்பருவ இலைக்கருகல்");
            textView2.setText(R.string.lateBlight3);
            textView3.setText(R.string.lateBlight4);

            break;
        case "septoriaLeafSpot":
            textView1.setText("செப்டோரியா இலைப்புள்ளி");
            textView2.setText(R.string.septoriaLeafSpot3);
            textView3.setText(R.string.septoriaLeafSpot4);
            break;
        case "tomato_mosaic":
            textView1.setText("தக்காளி தேமல் நோய்");
            textView2.setText(R.string.tomatoMosaic3);
            textView3.setText(R.string.tomatoMosaic4);
            break;
        case "yellowcurved":
            textView1.setText("இலை சுருட்டை நோய்");
            textView2.setText(R.string.yellowLeafCurl3);
            textView3.setText(R.string.yellowLeafCurl4);
            break;
        default:
    }
}
    }

    @Override
    public void onNothingSelected(AdapterView<?> parent) {

    }
}
