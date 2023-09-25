import { Injectable, inject } from '@angular/core';
import { Firestore, collection, collectionData, getDocs  } from '@angular/fire/firestore';
import { Observable, from } from 'rxjs';
import { map } from 'rxjs/operators';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class InvestigationsService {
  firestore: Firestore = inject(Firestore)
  investigations$: Observable<any[]>;

  constructor(private authService: AuthService) { }

  getInvestigationCollections(): Observable<any[]> {
    const userId = this.authService.userId;
    const investigationCollectionsRef = collection(this.firestore, 'investigations', userId, 'investigationCollections');
    
    // Convert the Promise returned by getDocs to an Observable using RxJS's from function
    return from(getDocs(investigationCollectionsRef)).pipe(
      map(snapshot => {
        const investigations = [];
        snapshot.forEach(doc => {
          investigations.push({ id: doc.id, ...doc.data() });
        });

        return investigations;
      })
    );
  }
}
