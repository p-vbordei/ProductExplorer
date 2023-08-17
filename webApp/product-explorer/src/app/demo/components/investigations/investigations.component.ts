import { Component, OnInit, OnDestroy } from '@angular/core';
import { ProductService } from '../../service/product.service';
import { Subscription } from 'rxjs';
import { LayoutService } from 'src/app/layout/service/app.layout.service';

@Component({
  selector: 'app-investigations',
  templateUrl: './investigations.component.html',
  styleUrls: ['./investigations.component.scss']
})
export class InvestigationsComponent implements OnInit, OnDestroy {

    investiations!: any;
    subscription!: Subscription;


    constructor(private productService: ProductService, public layoutService: LayoutService) {}

    ngOnInit() {
        this.initTables();
        //this.productService.getProductsSmall().then(data => this.products = data);

    }


    initTables() {
      this.investiations = [
        {
            "name": "AmazonBasics USB-C Cable",
            "asins": ["B01X234ABC", "B02Y789DEF"],
            "finished_timestamp": "2023-07-05T11:15:00",
            "started_timestamp": "2023-07-05T09:45:00",
            "status": "new",
            "id": 1
        },
        {
            "name": "Fire TV Stick",
            "asins": ["B03Z456GHI", "B04W891JKL"],
            "finished_timestamp": "2023-07-06T12:30:00",
            "started_timestamp": "2023-07-06T10:10:00",
            "status": "completed",
            "id": 2
        },
        {
           "name": "Echo Dot",
            "asins": ["B05M123NOP", "B06N456QRS"],
            "finished_timestamp": "2023-07-07T13:45:00",
            "started_timestamp": "2023-07-07T11:35:00",
            "status": "failed",
            "id": 3
        },
        {
            "name": "Kindle Paperwhite",
            "asins": ["B07T789TUV", "B08W012WXZ"],
            "finished_timestamp": "2023-07-08T14:00:00",
            "started_timestamp": "2023-07-08T12:50:00",
            "status": "completed",
            "id": 4
        },
        {
            "name": "Kindle Paperwhite",
            "asins": ["B09R345YAB", "B010567CDE"],
            "finished_timestamp": "2023-07-09T15:15:00",
            "started_timestamp": "2023-07-09T13:05:00",
            "status": "pending",
            "id": 5
        }
    ]
    }

    ngOnDestroy() {
        if (this.subscription) {
            this.subscription.unsubscribe();
        }
    }

}

