import { Component, OnInit, OnDestroy } from '@angular/core';
import { InvestigationsService } from '../../service/investigations';
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


    constructor(private investigationsService: InvestigationsService, public layoutService: LayoutService) {}

    ngOnInit() {
        this.initTables();
    }


    initTables() {
      this.subscription = this.investigationsService.getInvestigationCollections().subscribe((data: any) => {     
        this.investiations = data.map((entry: any) => {
            const res = {
                name: entry.name,
                asins: entry.asinList,
                investigationDate: new Date(entry.investigationDate.seconds * 1000),
                status: entry.status == "started" || entry.status == "finished" ?  entry.status : "pending",  
                id: entry.id
                } as any;
                
                return res;
            }); 
      });
    }

    ngOnDestroy() {
        if (this.subscription) {
            this.subscription.unsubscribe();
        }
    }

}

